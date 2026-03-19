import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    # LLM defaults
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    openai_api_key: str = ""

    # Agent behavior
    max_iterations: int = Field(default=10, ge=1, le=1000)
    max_total_tokens: int = Field(default=128_000, ge=1024)

    # VectorLink
    vectorlink_url: str = "http://localhost:8080"

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=os.environ.get("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_agent_settings() -> AgentConfig:
    return AgentConfig()


settings = get_agent_settings()
