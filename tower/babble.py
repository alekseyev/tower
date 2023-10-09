import json
import re
import time
from typing import Optional, Type

import openai
from pydantic import BaseModel
import spacy
from loguru import logger

from tower.settings import settings


openai.api_key = settings.GPT_TOKEN

json_pattern = re.compile(r"```(?:json)?(.*?)```", re.DOTALL)


class BabbleSentence(BaseModel):
    text: dict[str, str]  # {"en": "I went"}
    lemmas: dict[str, list[str]]  # {"en": ["I", "go"]}


nlp = {}
for code, model in settings.SPACY_MODELS.items():
    nlp[code] = spacy.load(model)
logger.info(f"Loaded {len(nlp)} Spacy models")


def lemmatize(lang_code: str, sentence: str) -> list[str]:
    doc = nlp[lang_code](sentence)
    return [token.lemma_ for token in doc]


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
        level: Optional[str] = None,
        N: int = 40,
        base_language: str = "Spanish",
    ) -> list[dict[str, str]]:
        prompt = (
            f"Here is a list of words in {base_language}: {', '.join(dictionary)}. "
            f"Generate {N} different sentences with these words"
        )
        if level:
            prompt += f", level {level}"
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
    level: Optional[str] = None,
    N: int = 40,
    base_language: str = "Spanish",
    source_class: Type = GPTSentences,
) -> list[BabbleSentence]:
    source = source_class()
    sentences = await source.generate_senteces(
        dictionary=dictionary,
        req_dictionary=req_dictionary,
        level=level,
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
