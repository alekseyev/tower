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
    "Agua",
    "Amigo",
    "Aquí",
    "Ayuda",
    "Bien",
    "Casa",
    "Comida",
    "Día",
    "Favor",
    "Gracias",
    "Hacer",
    "Hola",
    "Hombre",
    "Hoy",
    "Mal",
    "Mujer",
    "Necesitar",
    "No",
    "Poder",
    "Por",
    "Sentir",
    "Sí",
    "Tiempo",
    "Tu",
    "Yo",
    "Él",
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
            lemmas={"en": ["Hello", "My", "Friend"], "es": ["Hola", "Amigo"]},
        ),
        BabbleSentence(
            text={"en": "Thank you for your help.", "es": "Gracias por tu ayuda."},
            lemmas={"en": ["Thank", "You", "For", "Your", "Help"], "es": ["Gracias", "Por", "Tu", "Ayuda"]},
        ),
        BabbleSentence(
            text={"en": "Yes, I can do it.", "es": "Sí, puedo hacerlo."},
            lemmas={"en": ["Yes", "I", "Can", "Do", "It"], "es": ["Sí", "Poder", "Hacer", "Él"]},
        ),
        BabbleSentence(
            text={"en": "I feel good today.", "es": "Me siento bien hoy."},
            lemmas={"en": ["I", "Feel", "Good", "Today"], "es": ["Yo", "Sentir", "Bien", "Hoy"]},
        ),
        BabbleSentence(
            text={"en": "I need water.", "es": "Necesito agua."},
            lemmas={"en": ["I", "Need", "Water"], "es": ["Necesitar", "Agua"]},
        ),
    ]


def assert_same_sentences(sentence1: list[BabbleSentence], sentence2: list[BabbleSentence]):
    assert len(sentence1) == len(sentence2)
    for a, b in zip(sentence1, sentence2):
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

    sentences = await get_from_db(dictionary=["Yo", "Sentir", "Bien", "Hoy"])
    assert_same_sentences(sentences, [generated_output_with_lemmas[3]])


@pytest.mark.asyncio
async def test_skip_duplicates(generated_output_with_lemmas):
    await BabbleSentence(
        text={"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
        lemmas={"en": ["Hello", "My", "Friend"], "es": ["Hola", "Amigo"]},
    ).save()

    result = await generate_and_save_sentences(DICTIONARY)
    assert len(result) == 4
