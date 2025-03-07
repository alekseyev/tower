from unittest.mock import AsyncMock

import pytest

from backend.babble.babble import (
    BabbleSentence,
    GPTSentences,
    generate_and_save_sentences,
    generate_babble,
    get_from_db,
    get_sentences,
)

DICTIONARY = [
    "agua",
    "amigo",
    "aquí",
    "ayuda",
    "bien",
    "casa",
    "comida",
    "día",
    "favor",
    "gracias",
    "hacer",
    "hola",
    "hombre",
    "hoy",
    "mal",
    "mujer",
    "necesitar",
    "no",
    "poder",
    "por",
    "sentir",
    "sí",
    "tiempo",
    "tu",
    "yo",
    "él",
]


@pytest.fixture(autouse=True)
def mock_gpt_output(mocker):
    mocker.patch.object(
        GPTSentences,
        "generate_senteces",
        AsyncMock(
            return_value=[
                {"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
                {"en": "Thank you for your help.", "es": "Gracias por tu ayuda."},
                {"en": "Yes, I can do it.", "es": "Sí, puedo hacerlo."},
                {"en": "I feel good today.", "es": "Me siento bien hoy."},
                {"en": "I need water.", "es": "Necesito agua."},
            ]
        ),
    )


@pytest.fixture
def generated_output_with_lemmas():
    return [
        BabbleSentence(
            text={"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
            lemmas={"en": ["hello", "my", "friend"], "es": ["hola", "amigo"]},
        ),
        BabbleSentence(
            text={"en": "Thank you for your help.", "es": "Gracias por tu ayuda."},
            lemmas={"en": ["thank", "you", "for", "your", "help"], "es": ["gracias", "por", "tu", "ayuda"]},
        ),
        BabbleSentence(
            text={"en": "Yes, I can do it.", "es": "Sí, puedo hacerlo."},
            lemmas={"en": ["yes", "I", "can", "do", "it"], "es": ["sí", "poder", "hacer", "él"]},
        ),
        BabbleSentence(
            text={"en": "I feel good today.", "es": "Me siento bien hoy."},
            lemmas={"en": ["I", "feel", "good", "today"], "es": ["yo", "sentir", "bien", "hoy"]},
        ),
        BabbleSentence(
            text={"en": "I need water.", "es": "Necesito agua."},
            lemmas={"en": ["I", "need", "water"], "es": ["necesitar", "agua"]},
        ),
    ]


def assert_same_sentences(sentences1: list[BabbleSentence], sentences2: list[BabbleSentence]):
    assert len(sentences1) == len(sentences2)
    for a, b in zip(sentences1, sentences2):
        assert a.text == b.text
        assert a.lemmas == b.lemmas


@pytest.mark.asyncio
async def test_generate_sentences(generated_output_with_lemmas):
    result = await generate_babble(DICTIONARY)
    assert_same_sentences(result, generated_output_with_lemmas)


@pytest.mark.asyncio
async def test_get_sentences(generated_output_with_lemmas):
    result = await get_sentences(DICTIONARY, N=5)
    assert_same_sentences(result, generated_output_with_lemmas)


@pytest.mark.asyncio
async def test_get_from_db(generated_output_with_lemmas):
    await BabbleSentence.insert_many(generated_output_with_lemmas)

    sentences = await get_from_db(dictionary=["yo", "sentir", "bien", "hoy"])
    assert_same_sentences(sentences, [generated_output_with_lemmas[3]])


@pytest.mark.asyncio
async def test_skip_duplicates(generated_output_with_lemmas):
    await BabbleSentence(
        text={"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
        lemmas={"en": ["hello", "my", "friend"], "es": ["hola", "amigo"]},
    ).save()

    result = await generate_and_save_sentences(DICTIONARY)
    assert len(result) == 4
