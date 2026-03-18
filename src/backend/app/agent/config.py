from pydantic_settings import BaseSettings


class AgentConfig(BaseSettings):
    # LLM defaults
    default_provider: str = "openai"
    default_model: str = "gpt-4o"
    openai_api_key: str = ""

    # Agent behavior
    max_iterations: int = 10
    max_total_tokens: int = 128_000

    # VectorLink
    vectorlink_url: str = "http://localhost:8080"

    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"
