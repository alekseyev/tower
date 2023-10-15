from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from testcontainers.mongodb import MongoDbContainer

from app.app_ctx import AppCtx
from app.babble import BabbleSentence, GPTSentences, generate_babble, get_sentences
from app.settings import settings

DICTIONARY = [
    "yo",
    "tu",
    "hola",
    "gracias",
    "sí",
    "no",
    "por",
    "favor",
    "bien",
    "mal",
    "amigo",
    "agua",
    "comida",
    "casa",
    "tiempo",
    "día",
    "hombre",
    "mujer",
    "aquí",
    "sentir",
    "ayuda",
    "necesitar",
]



@pytest.fixture(autouse=True)
def mock_gpt_output(mocker):
    print("mock output")
    mocker.patch.object(
        GPTSentences,
        "generate_senteces",
        AsyncMock(
            return_value=[
                {"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
                {"en": "Thank you for your help.", "es": "Gracias por tu ayuda."},
                # {'en': 'Yes, I can do it.', 'es': 'Sí, puedo hacerlo.'},
                {"en": "I feel good today.", "es": "Me siento bien hoy."},
                {"en": "I need water.", "es": "Necesito agua."},
            ]
        ),
    )


@pytest.fixture
def generated_output_with_lemmas():
    print("mock lemmas")
    return [
        BabbleSentence(
            text={"en": "Hello, my friend!", "es": "¡Hola, amigo!"},
            lemmas={"en": ["hello", "my", "friend"], "es": ["Hola", "amigo"]},
        ),
        BabbleSentence(
            text={"en": "Thank you for your help.", "es": "Gracias por tu ayuda."},
            lemmas={"en": ["thank", "you", "for", "your", "help"], "es": ["gracias", "por", "tu", "ayuda"]},
        ),
        # BabbleSentence(
        #     text={"en": "Yes, I can do it.", "es": "Sí, puedo hacerlo."},
        #     lemmas={"en": ["yes", "I", "can", "do", "it"], "es": ["sí", "poder", "hacer él"]},
        # ),
        # TODO hacer el -> hacer, el
        BabbleSentence(
            text={"en": "I feel good today.", "es": "Me siento bien hoy."},
            lemmas={"en": ["I", "feel", "good", "today"], "es": ["yo", "sentir", "bien", "hoy"]},
        ),
        BabbleSentence(
            text={"en": "I need water.", "es": "Necesito agua."},
            lemmas={"en": ["I", "need", "water"], "es": ["necesitar", "agua"]},
        ),
    ]


@pytest.mark.asyncio
async def test_generate_sentences(generated_output_with_lemmas):
    result = await generate_babble(DICTIONARY)
    assert result == generated_output_with_lemmas


@pytest.mark.asyncio
async def test_get_sentences(generated_output_with_lemmas):
    result = await get_sentences(DICTIONARY, N=4)
    assert result == generated_output_with_lemmas
