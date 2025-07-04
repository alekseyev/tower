import time
from uuid import UUID

from beanie import Document
from pydantic import BaseModel

from backend.babble.models import BabbleSentence
from backend.courses.courses import get_base_words, get_new_words

TRACK_CORRECTNESS = 10
TRACK_LAST_EXERCISES = 100

EXERCISES_PER_LESSON = 8
WORDS_TO_PRACTICE_PER_LESSON = 4


class WordData(BaseModel):
    seen_times: int = 0
    last_seen_ts: int = 0
    first_seen_ts: int = 0
    correctness_last_times: list[bool] = []  # for the last 10 times user seen word, did the user use it correctly
    correctness_rate: int = 0  # percentage based on correctness_last_times

    def add_seen(self, correct: bool | None = None):
        ts = int(time.time())
        self.last_seen_ts = ts
        if not self.first_seen_ts:
            self.first_seen_ts = ts
        self.seen_times += 1
        if correct is not None:
            self.correctness_last_times.append(correct)
            self.correctness_last_times = self.correctness_last_times[-TRACK_CORRECTNESS:]
            self.correctness_rate = sum(self.correctness_last_times) * 100 // len(self.correctness_last_times)


class LanguageData(BaseModel):
    courses: list[str] = ["casa.s01e01"]
    words: dict[str, WordData] = {}
    first_exercise_ts: int = 0
    last_exercise_ts: int = 0
    last_new_word_ts: int = 0
    active_courses: list[str] = []
    total_exercises: int = 0
    last_exercises: list[UUID] = []

    def add_new_words(self, words: list[str]):
        ts = int(time.time())
        self.last_new_word_ts = ts
        for word in words:
            if word not in self.words:
                self.words[word] = WordData()
            self.words[word].add_seen()

    def add_exercise(self, id: UUID, words: list[str], correct: bool = True):
        ts = int(time.time())
        if not self.first_exercise_ts:
            self.first_exercise_ts = ts
        self.last_exercise_ts = ts
        self.total_exercises += 1
        new_words = [word for word in words if word not in self.words]
        self.add_new_words(new_words)
        for word in words:
            self.words[word].add_seen(correct)
        self.last_exercises.append(id)
        self.last_exercises = self.last_exercises[-TRACK_LAST_EXERCISES:]

    def get_new_words(self, max_seen_count=5) -> set[str]:
        # Return new words (seen count < 5)
        return set(word for word, data in self.words.items() if data.seen_times < max_seen_count)

    def get_bad_words(self, max_correctness_rate=85) -> set[str]:
        return set(word for word, data in self.words.items() if data.correctness_rate < max_correctness_rate)

    def suggest_words_to_practice(self, N: int = WORDS_TO_PRACTICE_PER_LESSON) -> set[str]:
        suggested = set()

        # 1. New words (seen count < 5)
        new_words = sorted(self.get_new_words(), key=lambda w: self.words[w].seen_times, reverse=True)
        while len(suggested) < N and new_words:
            suggested.add(new_words.pop())

        # 2. Bad corretness rate
        bad_words = sorted(self.get_bad_words(), key=lambda w: self.words[w].correctness_rate, reverse=True)
        while len(suggested) < N and bad_words:
            suggested.add(bad_words.pop())

        # 3. Last seen
        if len(suggested) < N:
            words = sorted(self.words.keys(), key=lambda w: self.words[w].last_seen_ts, reverse=True)

            while len(suggested) < N:
                suggested.add(words.pop())

        return suggested


class UserProgress(Document):
    id: UUID
    languages: dict[str, LanguageData] = {}

    def get_new_words(self, lang: str, course: str, N: int = 5) -> list[str]:
        if lang not in self.languages:
            self.languages[lang] = LanguageData()
            self.languages[lang].add_new_words(get_base_words(lang))
        current_words = list(self.languages[lang].words.keys())
        return get_new_words(lang, course, current_words, N=N)

    async def get_sentences(self, lang: str, N: int = EXERCISES_PER_LESSON) -> list[BabbleSentence]:
        from backend.babble.babble import get_sentences

        suggested = self.languages[lang].suggest_words_to_practice()
        sentences = []
        for word in suggested:
            sentences += await get_sentences(
                dictionary=list(self.languages[lang].words.keys()),
                req_dictionary=[word],
                base_language=lang,
                exclude_ids=self.languages[lang].last_exercises,
                N=N // len(suggested),
            )

        return sentences

    class Settings:
        name = "user_progress"


class ExerciseResult(BaseModel):
    user_id: UUID
    lang: str
    results: dict[UUID, bool]


class NewWordsRequest(BaseModel):
    user_id: UUID
    lang: str
    course: str


class Exercise(BaseModel):
    type: str
    sentence: BabbleSentence | None
    base_lang: str
    dictionary: dict[str, list[str]]
    new_word: str | None = None
    matches: dict[str, str] = {}


courses_models = [UserProgress]
