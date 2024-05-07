import spacy

from app.settings import settings


def download_spacy_models():
    for model in settings.SPACY_MODELS.values():
        spacy.cli.download(model)


if __name__ == "__main__":
    download_spacy_models()
