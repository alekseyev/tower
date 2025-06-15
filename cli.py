import asyncio
import json
from collections import Counter
from functools import wraps

import typer
from bs4 import BeautifulSoup
from loguru import logger

from backend.app_ctx import get_application_ctx
from backend.core.models import User
from backend.dictionary.words import generate_and_save_translations, get_translations_from_db

app = typer.Typer()


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@app.command()
def process_srt(filename: str):
    state = "waiting_ts"
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if state == "waiting_ts" and "-->" in line:
                state = "processing_lines"
                continue

            if state == "processing_lines" and not line:
                state = "waiting_ts"
                continue

            if state == "processing_lines":
                soup = BeautifulSoup(line)
                print(soup.get_text())


@app.command()
def process_words(filename: str, lang: str = "es"):
    from backend.babble.babble import lemmatize

    lemmatized = []
    with open(filename, "r") as f:
        for line in f:
            lemmatized += lemmatize(lang, line, skip_propns=True)

    counts = Counter(lemmatized)
    print(json.dumps(dict(counts.most_common()), indent=4))


@app.command()
@coro
async def generate_base_sentences(lang: str = "es"):
    from backend.babble.babble import generate_and_save_sentences

    with open(f"{lang}/base.json", "r") as f:
        words = json.load(f)

    logger.info(f"Generating sentences for {lang} with words: {', '.join(words)}")

    async with get_application_ctx():
        result = await generate_and_save_sentences(dictionary=words, base_language=lang, N=40)

    logger.info(f"{len(result)} sentences generated")


@app.command()
@coro
async def generate_course_sentences(course: str, lang: str = "es", limit: int = 1000):
    from backend.babble.babble import get_sentences

    with open(f"{lang}/base.json", "r") as f:
        base_dict = json.load(f)

    with open(f"{lang}/{course}.json", "r") as f:
        course_data = json.load(f)

    course_words = list(course_data.keys())[:limit]

    logger.info(f"Generating sentences for {lang}: {len(base_dict)} base words, {len(course_words)} course words")

    async with get_application_ctx():
        current_dictionary = base_dict
        current_req = []
        total = 0

        for word in course_words:
            current_req = [word]
            current_dictionary += current_req
            result = await get_sentences(
                dictionary=current_dictionary,
                req_dictionary=current_req,
                base_language=lang,
                N=10,
                maximum_passes=20,
            )
            total += len(result)

    logger.info(f"{len(result)} correct sentences generated")


@app.command()
@coro
async def get_translations(course: str, lang: str = "es", limit: int = 1000):
    with open(f"{lang}/{course}.json", "r") as f:
        course_data = json.load(f)

    course_words = list(course_data.keys())[:limit]

    logger.info(f"Generating translations for {lang}: {len(course_words)} course words")

    async with get_application_ctx():
        for i, word in enumerate(course_words):
            from_api = False
            translations = await get_translations_from_db(word, lang, "en")
            while translations is None:
                from_api = True
                try:
                    translations = await generate_and_save_translations(word, lang, "en")
                except Exception as e:
                    logger.warning(f"Error: {e}")
                    await asyncio.sleep(60)
            logger.info(f"{i: 3}. {word}: {', '.join(translations)}")
            if from_api:
                await asyncio.sleep(1800)


@app.command()
@coro
async def create_user(nickname: str):
    async with get_application_ctx():
        user = await User.create_user(nickname)
        logger.info(f"User created: {user}")


if __name__ == "__main__":
    app()
