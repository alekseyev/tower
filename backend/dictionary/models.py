from beanie import Document
from pydantic import BaseModel, Field

from backend.settings import settings

DICTIONARIES = {}


class IdOnlyView(BaseModel):
    id: str = Field(alias="_id")


class BaseDictionary(Document):
    id: str
    translations: dict[str, list[str]]  # {"en": ["the", "he"]}

    @classmethod
    async def get_all_words(cls) -> list[str]:
        data = await cls.find_all().project(IdOnlyView).to_list()
        return [doc.id for doc in data]


class EnglishDictionary(BaseDictionary):
    class Settings:
        name = "dictionary_en"


DICTIONARIES["en"] = EnglishDictionary


if "es" in settings.LANGUAGES:

    class SpanishDictionary(BaseDictionary):
        class Settings:
            name = "dictionary_es"

    DICTIONARIES["es"] = SpanishDictionary


if "fr" in settings.LANGUAGES:

    class FrenchDictionary(BaseDictionary):
        class Settings:
            name = "dictionary_fr"

    DICTIONARIES["fr"] = FrenchDictionary


if "uk" in settings.LANGUAGES:

    class UkrainianDictionary(BaseDictionary):
        class Settings:
            name = "dictionary_ua"

    DICTIONARIES["uk"] = UkrainianDictionary


words_models = list(DICTIONARIES.values())
