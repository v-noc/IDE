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
    GEMINI_API_KEY: str

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
    It also ensures that the test environment variables are loaded if APP_ENV is set to 'test'.
    """
    env_file = os.environ.get("ENV_FILE", ".env")
    if os.environ.get("APP_ENV") == "test":
        # In a test environment, construct the absolute path to tests/.env.test
        # Assumes the script is run from the project root.
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / "tests" / ".env.test"
    
    return Settings(_env_file=env_file)
