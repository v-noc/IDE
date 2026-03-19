"""LLM call parameters for chat turns (REST and executor share this model)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatCompletionParams(BaseModel):
    """
    Overrides for a single assistant generation.
    Omitted fields fall back to `AgentConfig` / provider defaults.
    """

    model_config = ConfigDict(extra="ignore")

    provider: str | None = Field(
        default=None,
        description="Registered provider name, e.g. openai",
    )
    model: str | None = Field(
        default=None,
        description="Provider model id, e.g. gpt-4o-mini",
    )
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128_000)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: float | None = Field(default=None, ge=-2.0, le=2.0)
    stop: list[str] | None = Field(default=None, max_length=8)

    def provider_create_kwargs(self) -> dict:
        """Keyword args for `LLMFactory.create` / ChatOpenAI (excluding provider+model)."""
        return self.model_dump(
            exclude={"provider", "model"},
            exclude_none=True,
        )
