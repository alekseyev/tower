from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field


class BabbleSentence(Document):
    id: UUID = Field(default_factory=uuid4)
    text: dict[str, str]  # {"en": "I went"}
    lemmas: dict[str, list[str]]  # {"en": ["I", "go"]}

    class Settings:
        name = "babble"


babble_models = [BabbleSentence]
