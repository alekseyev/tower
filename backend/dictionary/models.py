import unicodedata

from beanie import Document
from pydantic import BaseModel, Field

from backend.settings import settings

DICTIONARIES = {}


class WordOnlyView(BaseModel):
    id: str = Field(alias="_id")
    normalized: str | None = None


def remove_accents(text: str):
    normalized_text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized_text if unicodedata.category(char) != "Mn")


class BaseDictionary(Document):
    id: str
    normalized: str | None = None
    translations: dict[str, list[str]]  # {"en": ["the", "he"]}

    @classmethod
    async def get_all_words(cls, include_normalized: bool = True) -> list[str]:
        data = await cls.find_all().project(WordOnlyView).to_list()
        by_ids = [doc.id for doc in data]
        by_norm = []
        if include_normalized:
            by_norm = [doc.normalized for doc in data if doc.normalized and doc.normalized != doc.id]
        return by_ids + by_norm

    @classmethod
    async def get_translations(cls, words: list[str], to_lang: str = "en") -> dict[str, list[str]]:
        data = await cls.find({"_id": {"$in": words}}).to_list()
        return {translation.id: translation.translations[to_lang] for translation in data}

    async def save(self, *args, **kwargs):
        self.normalized = remove_accents(self.id)
        await super().save(*args, **kwargs)


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
