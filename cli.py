from collections import Counter
import json
from bs4 import BeautifulSoup
import spacy
import typer
from app.babble import lemmatize

from app.settings import settings

app = typer.Typer()


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
    with open(filename, "r") as f:
        text = f.read()

    words = text.split()
    words = [w.strip(".,¿?¡!:;()-\"").lower() for w in words]
    lemmatized = []
    for word in words:
        if not word or word.isnumeric():
            continue
        lemmatized += lemmatize(lang, word)

    counts = Counter(lemmatized)
    print(json.dumps(dict(counts.most_common()), indent=4))


if __name__ == "__main__":
    app()
