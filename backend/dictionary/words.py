import asyncio

from deep_translator import LingueeTranslator
from deep_translator.exceptions import ElementNotFoundInGetRequest
from loguru import logger

from backend.dictionary.models import DICTIONARIES
from backend.settings import settings


def get_translations_online(word: str, source: str, target: str) -> list[str]:
    try:
        translator = LingueeTranslator(
            source=settings.LANGUAGES[source].lower(), target=settings.LANGUAGES[target].lower()
        )
        return translator.translate(word, return_all=True)
    except ElementNotFoundInGetRequest:
        return []


async def get_translations_from_db(word: str, source: str, target: str) -> list[str] | None:
    word_doc = await DICTIONARIES[source].get(word)
    if word_doc and target in word_doc.translations:
        return word_doc.translations[target]


async def generate_and_save_translations(word: str, source: str, target: str) -> list[str]:
    loop = asyncio.get_running_loop()
    translations = await loop.run_in_executor(None, get_translations_online, word, source, target)
    word_doc = await DICTIONARIES[source].get(word)
    if not word_doc:
        word_doc = DICTIONARIES[source](id=word, translations={})
    word_doc.translations[target] = translations
    await word_doc.save()
    return translations


async def get_translations(word: str, source: str, target: str) -> list[str]:
    translations = await get_translations_from_db(word, source, target)
    if translations is None:
        logger.info(f"Not found translation for {word}({source}), getting from Linquee")
        return await generate_and_save_translations(word, source, target)
    return translations
