import asyncio
import time
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field

TRACK_CORRECTNESS = 10


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
    first_lesson_ts: int = 0
    last_lesson_ts: int = 0
    last_new_word_ts: int = 0
    active_courses: list[str] = []
    total_lessons: int = 0

    def add_new_words(self, words: list[str]):
        ts = int(time.time())
        self.last_new_word_ts = ts
        for word in words:
            if word not in self.words:
                self.words[word] = WordData()
            self.words[word].add_seen()


class UserProgress(Document):
    user_id: UUID
    languages: dict[str, LanguageData] = {}

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
            UserProgress(user_id=user.id).insert(),
        )

        return user


beanie_models = [BabbleSentence, User, UserProgress]
