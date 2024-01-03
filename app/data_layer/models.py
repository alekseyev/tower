import asyncio
import time
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field

from app.courses import get_base_words, get_new_words

TRACK_CORRECTNESS = 10
TRACK_LAST_EXERCISES = 40


class BabbleSentence(Document):
    id: UUID = Field(default_factory=uuid4)
    text: dict[str, str]  # {"en": "I went"}
    lemmas: dict[str, list[str]]  # {"en": ["I", "go"]}

    class Settings:
        name = "babble"


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


class UserProgress(Document):
    id: UUID
    languages: dict[str, LanguageData] = {}

    def get_new_words(self, lang: str, course: str) -> list[str]:
        if lang not in self.languages:
            self.languages[lang] = LanguageData()
            self.languages[lang].add_new_words(get_base_words(lang))
        current_words = list(self.languages[lang].words.keys())
        return get_new_words(lang, course, current_words)

    async def get_sentences(self, lang: str) -> list[BabbleSentence]:
        from app.babble import get_sentences

        return await get_sentences(
            dictionary=list(self.languages[lang].words.keys()),
            base_language=lang,
            exclude_ids=self.languages[lang].last_exercises,
            N=5,
        )

    class Settings:
        name = "user_progress"


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    nickname: str

    class Settings:
        name = "users"

    @classmethod
    async def create_user(cls, nickname: str) -> "User":
        user = User(nickname=nickname)
        await asyncio.gather(
            user.insert(),
            UserProgress(id=user.id).insert(),
        )

        return user


beanie_models = [BabbleSentence, User, UserProgress]
