import json
import re
import time
from typing import Optional, Type

import openai
import spacy
from bson import ObjectId
from loguru import logger

from app.data_layer.models import BabbleSentence
from app.settings import settings

openai.api_key = settings.GPT_TOKEN

json_pattern = re.compile(r"```(?:json)?(.*?)```", re.DOTALL)


nlp = {}
start = time.perf_counter()
for code, model in settings.SPACY_MODELS.items():
    nlp[code] = spacy.load(model)
logger.info(f"Loaded {len(nlp)} Spacy models in {time.perf_counter() - start:.6}s")


def lemmatize(lang_code: str, sentence: str) -> list[str]:
    doc = nlp[lang_code](sentence)
    return [token.lemma_.capitalize() for token in doc if token.lemma_ not in ".,¿?¡!:;()"]


class GPTSentences:
    token: str
    model: str
    lang_codes: dict[str, str]

    def __init__(self):
        self.token = settings.GPT_TOKEN
        self.model = settings.GPT_MODEL
        self.lang_codes = settings.LANGUAGES

    async def generate_senteces(
        self,
        dictionary: list[str],
        req_dictionary: Optional[list[str]] = None,
        base_language: str = "es",
        N: int = 40,
    ) -> list[dict[str, str]]:
        prompt = (
            f"Here is a list of words in {self.lang_codes[base_language]}: {', '.join(dictionary)}. "
            f"Generate {N} different sentences with these words"
        )
        if req_dictionary:
            prompt += ", but each sentence absolutely must contain at least" " one word from this list: "
            prompt += ", ".join(req_dictionary)
        prompt += ". Return as a JSON list, with these fields for each: "
        prompt += ", ".join(f"{code} - sentence in {language}" for code, language in self.lang_codes.items())

        schema = {
            "type": "object",
            "properties": {
                "sentences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            code: {"type": "string", "description": f"Sentence in {language}"}
                            for code, language in self.lang_codes.items()
                        },
                    },
                }
            },
        }

        logger.info(
            f"Calling OpenAI API model {self.model} to generate {N} sentences in {len(self.lang_codes)} languages..."
        )

        start = time.perf_counter()
        completion = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a language tutor"},
                {"role": "user", "content": prompt},
            ],
            functions=[
                {"name": "fn_sentences", "parameters": schema},
            ],
        )
        usage = completion.usage
        response_message = completion["choices"][0]["message"]

        hacks = []

        if response_message.get("function_call"):
            content = response_message.function_call.arguments
            hacks.append("function_args")
        else:
            content = response_message.content
            hacks.append("content")

        if "```" in content:
            match = json_pattern.search(content)
            if match:
                content = match.group(1)
            hacks.append("markdown")

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            result = []
            logger.error(f"Unable to parse result! Content: {content}")

        if isinstance(result, dict):
            hacks.append("dict")
            result = next(iter(result.values()))

        logger.info(
            f"OpenAPI {self.model} call took {time.perf_counter() - start:.6}s, returning {len(result)} sentences. "
            f"Hacks applied: {hacks}. "
            f"API usage: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}"
        )

        return result


async def generate_babble(
    dictionary: list[str],
    req_dictionary: Optional[list[str]] = None,
    base_language: str = "es",
    N: int = 40,
    source_class: Type = GPTSentences,
) -> list[BabbleSentence]:
    source = source_class()
    sentences = await source.generate_senteces(
        dictionary=dictionary,
        req_dictionary=req_dictionary,
        N=N,
        base_language=base_language,
    )

    start = time.perf_counter()
    result = [
        BabbleSentence(
            text={lang: sentence for lang, sentence in sentence.items()},
            lemmas={lang: lemmatize(lang, sentence) for lang, sentence in sentence.items()},
        )
        for sentence in sentences
    ]
    logger.info(f"Tokenized {len(sentences)} sentences in {time.perf_counter() - start:.6}s")
    return result


async def get_from_db(
    dictionary: list[str],
    req_dictionary: list[str] | None = None,
    base_language: str = "es",
    N: int = 10,
    exclude_ids: list[ObjectId] | None = None,
) -> list[BabbleSentence]:
    subqueries = [{"$expr": {"$setIsSubset": [f"$lemmas.{base_language}", dictionary]}}]
    if exclude_ids:
        subqueries.append({"_id": {"$nin": exclude_ids}})
    if req_dictionary:
        subqueries.append({f"lemmas.{base_language}": {"$in": req_dictionary}})

    return await BabbleSentence.find({"$and": subqueries}).to_list()


async def generate_and_save_sentences(
    dictionary: list[str],
    req_dictionary: Optional[list[str]] = None,
    base_language: str = "es",
    N: int = 10,
) -> list[BabbleSentence]:
    sentences = await generate_babble(
        dictionary=dictionary,
        req_dictionary=req_dictionary,
        base_language=base_language,
        N=N,
    )

    found_sentences_result = await BabbleSentence.find(
        {"text.{base_language}": {"$in": [sentence.text[base_language] for sentence in sentences]}}
    ).to_list()

    found_sentences = [sentence.text[base_language] for sentence in found_sentences_result]

    sentences = [sentence for sentence in sentences if sentence.text[base_language] not in found_sentences]

    await BabbleSentence.insert_many(sentences)
    return sentences


async def get_sentences(
    dictionary: list[str],
    req_dictionary: list[str] | None = None,
    base_language: str = "es",
    N: int = 10,
    exclude_ids: list[ObjectId] | None = None,
) -> list[BabbleSentence]:
    if req_dictionary is None:
        req_dictionary = []
    sentences = await get_from_db(
        dictionary=dictionary,
        req_dictionary=req_dictionary,
        base_language=base_language,
        N=N,
        exclude_ids=exclude_ids,
    )

    while len(sentences) < N:
        to_generate = 40
        dict_len = len(dictionary) + len(req_dictionary)
        if dict_len < 50:
            to_generate = 30
            if dict_len < 20:
                to_generate = 20
            if dict_len < 10:
                to_generate = 10
            N = min(to_generate, N)

        sentences += await generate_and_save_sentences(
            dictionary=dictionary,
            req_dictionary=req_dictionary,
            base_language=base_language,
            N=to_generate,
        )

    return sentences
