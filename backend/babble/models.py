from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field

from backend.babble.lemmas import lemmatize


class BabbleSentence(Document):
    id: UUID = Field(default_factory=uuid4)
    text: dict[str, str]  # {"en": "I went"}
    lemmas: dict[str, list[str]] = {}  # {"en": ["I", "go"]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.lemmas:
            self.update_lemmas()

    def update_lemmas(self):
        self.lemmas = {lang: lemmatize(lang, sentence) for lang, sentence in self.text.items()}

    class Settings:
        name = "babble"


babble_models = [BabbleSentence]
