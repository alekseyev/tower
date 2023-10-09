from collections import defaultdict
import json


from pydantic_settings import BaseSettings, SettingsConfigDict

secrets = defaultdict(str)

try:
    with open("secrets.json", "r") as f:
        secrets = json.load(f)
except FileNotFoundError:
    pass


class Settings(BaseSettings):
    DEBUG: bool = False

    GPT_TOKEN: str = secrets["openai_token"]
    GPT_MODEL: str = "gpt-3.5-turbo"

    SPACY_MODELS: dict[str, str] = {
        "en": "en_core_web_sm",
        "es": "es_core_news_sm",
        "fr": "fr_core_news_sm",
        "uk": "uk_core_news_sm",
    }

    LANGUAGES: dict[str, str] = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "uk": "Ukrainian",
    }

    model_config = SettingsConfigDict(env_prefix="SET_")


settings = Settings()
