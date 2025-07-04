import time

import spacy
from loguru import logger

from backend.settings import settings

nlp = {}
start = time.perf_counter()
for code, model in settings.SPACY_MODELS.items():
    nlp[code] = spacy.load(model)
logger.info(f"Loaded {len(nlp)} Spacy models in {time.perf_counter() - start:.6}s")


EXCEPTIONS = {
    "es": {"hablas": "hablar", "señoritar": "señorita"},
    "en": {},
}

FAKE_PROPNS = {
    "es": [
        "Hola",
        "Y",
        "EN",
        "De",
        "Que",
        "Ah",
        "A",
        "Por",
        "Vamos",
        "Pero",
        "En",
        "O",
        "Al",
        "Bueno",
        "Con",
        "Pues",
        "Sí",
        "Para",
        "Venga",
        "Si",
        "ENTRE",
        "Joder",
        "Como",
        "Eh",
        "Ni",
        "DE",
        "Porque",
        "Oh",
        "Sin",
        "Uf",
        "Ay",
        "QUE",
        "Señores",
        "Chist",
        "Oye",
        "Ve",
        "Cuando",
        "AL",
        "Bájeme",
        "Fuego",
        "Hasta",
        "Alto",
        "Escucha",
        "Quieto",
        "Dámelo",
        "Siéntate",
        "Tranquilos",
        "Uy",
        "Basta",
        "DEL",
        "Caramba",
        "Según",
        "Te",
        "Coño",
        "Tú",
        "Perfecto",
        "Adiós",
        "Bájame",
        "Profesor",
        "Aunque",
        "Gracias",
        "Amigo",
        "Dios",
        "POR",
        "Viva",
        "Jacinto",
        "Va",
        "Cúbreme",
        "CON",
        "Sentaos",
        "Uh",
    ],
    "en": [],
}


STOP_WORDS = {
    "es": ["eh", "coño", "puta"],
    "en": [],
}


def process_exceptions(lang_code: str, word: str) -> str:
    if word in FAKE_PROPNS[lang_code]:
        return word.lower()
    return EXCEPTIONS.get(lang_code, {}).get(word, word)


def lemmatize(
    lang_code: str,
    sentence: str,
    skip_propns: bool = False,
    skip_words: list | None = None,
) -> list[str]:
    if not skip_words:
        skip_words = STOP_WORDS.get(lang_code, [])
    doc = nlp[lang_code](sentence)
    l_doc = nlp[lang_code](sentence.lower())
    lemmas = []
    for token, l_token in zip(doc, l_doc):
        if not token.is_alpha:
            continue
        # Avoid wrongly detecting capitalized words as PROPN (e.g. Hola amigo -> hola should be VERB, not PROPN)
        # Except this doesn't catch "hola", so we also have a list of fake propns
        if token.pos_ == "PROPN" and token.lemma_[0].isupper() and l_token.pos_ != "PROPN":
            token = l_token
        if skip_propns and token.pos_ == "PROPN" and token.lemma_ not in FAKE_PROPNS[lang_code]:
            continue
        lemmas += [process_exceptions(lang_code, word) for word in token.lemma_.split() if word not in skip_words]
    return lemmas
