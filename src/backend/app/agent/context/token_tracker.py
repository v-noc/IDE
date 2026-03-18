from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel
from typing import Optional


class TokenUsage(BaseModel):
    """Accumulated token usage for a single run."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: Optional[str] = None


class TokenTracker(BaseCallbackHandler):
    """LangChain callback handler that accumulates token usage across calls."""

    def __init__(self, max_total_tokens: int = 128_000):
        self.max_total_tokens = max_total_tokens
        self.usage = TokenUsage()

    def on_llm_end(self, response, **kwargs):
        """Called after each LLM invocation — accumulates usage."""
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            self.usage.prompt_tokens += usage.get("prompt_tokens", 0)
            self.usage.completion_tokens += usage.get("completion_tokens", 0)
            self.usage.total_tokens += usage.get("total_tokens", 0)

    @property
    def remaining(self) -> int:
        return self.max_total_tokens - self.usage.total_tokens

    @property
    def over_budget(self) -> bool:
        return self.usage.total_tokens >= self.max_total_tokens

    def get_usage(self) -> TokenUsage:
        return self.usage.model_copy()
