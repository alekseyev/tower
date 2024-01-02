import asyncio
import json
from collections import Counter
from functools import wraps

import spacy
import typer
from bs4 import BeautifulSoup
from loguru import logger

from app.app_ctx import get_application_ctx
from app.data_layer.models import User
from app.settings import settings

app = typer.Typer()


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@app.command()
def download_spacy_models():
    for model in settings.SPACY_MODELS.values():
        spacy.cli.download(model)


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
    from app.babble import lemmatize

    with open(filename, "r") as f:
        text = f.read()

    words = text.split()
    words = [w.strip('.,¿?¡!:;()-"').lower() for w in words]
    lemmatized = []
    for word in words:
        if not word or word.isnumeric():
            continue
        lemmatized += lemmatize(lang, word)

    counts = Counter(lemmatized)
    print(json.dumps(dict(counts.most_common()), indent=4))


@app.command()
@coro
async def generate_base_sentences(lang: str = "es"):
    from app.babble import generate_and_save_sentences

    with open(f"{lang}/base.json", "r") as f:
        words = json.load(f)

    logger.info(f"Generating sentences for {lang} with words: {', '.join(words)}")

    async with get_application_ctx():
        result = await generate_and_save_sentences(dictionary=words, base_language=lang, N=40)

    logger.info(f"{len(result)} sentences generated")


@app.command()
@coro
async def generate_course_sentences(filename: str, lang: str = "es"):
    from app.babble import generate_and_save_sentences

    with open(f"{lang}/base.json", "r") as f:
        base_dict = json.load(f)

    with open(filename, "r") as f:
        course_data = json.load(f)

    course_words = list(course_data.keys())

    logger.info(f"Generating sentences for {lang}: {len(base_dict)} base words, {len(course_words)} course words")

    async with get_application_ctx():
        current_dictionary = base_dict
        current_req = []
        total = 0

        for word in course_words:
            if word in current_dictionary:
                continue

            current_req.append(word)
            if len(current_req) >= 5:
                result = await generate_and_save_sentences(
                    dictionary=current_dictionary, req_dictionary=current_req, base_language=lang, N=20
                )
                for sentence in result:
                    total += 1
                    logger.info(f"{total}. {sentence.text[lang]}")
                current_dictionary += current_req
                current_req = []

        if current_req:
            result = await generate_and_save_sentences(
                dictionary=current_dictionary, req_dictionary=current_req, base_language=lang, N=20
            )
            for sentence in result:
                total += 1
                logger.info(f"{total}. {sentence[lang]}")

    logger.info(f"{len(result)} sentences generated")


@app.command()
@coro
async def create_user(nickname: str):
    async with get_application_ctx():
        user = await User.create_user(nickname)
        logger.info(f"User created: {user}")


if __name__ == "__main__":
    app()
