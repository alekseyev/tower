import spacy
import typer

from tower.settings import settings

app = typer.Typer()


@app.command()
def download_spacy_models():
    for model in settings.SPACY_MODELS.values():
        spacy.cli.download(model)


@app.command()
def dummy():
    ...


if __name__ == "__main__":
    app()
