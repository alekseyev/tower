from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = False

    BACKEND_URL: str = "http://127.0.0.1:8000"
    LOCAL_STORAGE_PREFIX: str = "tower.learn_app"

    model_config = SettingsConfigDict(env_prefix="UI_")


settings = Settings()
