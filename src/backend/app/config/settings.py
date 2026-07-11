import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str

    TERMINUS_HOST: str
    TERMINUS_USER: str
    TERMINUS_KEY: str
    TERMINUS_TEAM: str
    TERMINUS_DB: str

    LOG_LEVEL: str = "INFO"

    # fastapi-cache2 + Redis. If false, use a no-op backend.
    ENABLE_CACHE: bool = False
    REDIS_URL: Optional[str] = None
    CACHE_PREFIX: str = "vnoc-cache"

    # Optional JSON-RPC URLs for language drivers (loaded from the same .env as above).
    VNOC_LSP_PYTHON_URL: Optional[str] = None
    VNOC_LSP_TS_JS_URL: Optional[str] = None

    # provider[:model] — the only LLM switch (plan backend/02)
    WALKTHROUGH_LLM: str = "fake"
    OPENAI_API_KEY: Optional[str] = None
    AI_GATEWAY_API_KEY: Optional[str] = None
    CUSTOM_LLM_BASE_URL: Optional[str] = None
    CUSTOM_LLM_API_KEY: Optional[str] = None

    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "v-noc-walkthrough"

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
