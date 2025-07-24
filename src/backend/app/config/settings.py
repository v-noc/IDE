import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    APP_ENV: str
    ARANGO_HOST: str
    ARANGO_USER: str
    ARANGO_PASSWORD: str
    ARANGO_DB: str
    ARANGO_ROOT_PASSWORD: str
    PORT: int

    model_config = SettingsConfigDict(
        # Pydantic-Settings will automatically use the ENV_FILE env var if it exists.
        # Otherwise, it will fall back to ".env".
        env_file=os.environ.get("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def is_test(self) -> bool:
        return self.APP_ENV == "test"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached, singleton instance of the Settings.
    This function will only create the Settings object once.
    """
    return Settings()
