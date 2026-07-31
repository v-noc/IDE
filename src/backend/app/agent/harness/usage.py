from __future__ import annotations

from typing import Any

from app.agent.schemas.conversation import TokenUsage


# Rough USD per 1M tokens — honest ballpark for display, not billing.
_PRICE_PER_MTOK: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-5": (1.25, 10.00),
    "gpt-5-mini": (0.25, 2.00),
}


def extract_usage(message: Any) -> TokenUsage | None:
    """Pull TokenUsage from a LangChain AIMessage / chunk if present."""
    raw = getattr(message, "usage_metadata", None)
    if not raw and hasattr(message, "response_metadata"):
        meta = getattr(message, "response_metadata") or {}
        raw = meta.get("token_usage") or meta.get("usage")
    if not raw:
        return None
    if isinstance(raw, dict):
        return TokenUsage(
            input_tokens=int(
                raw.get("input_tokens")
                or raw.get("prompt_tokens")
                or 0
            ),
            output_tokens=int(
                raw.get("output_tokens")
                or raw.get("completion_tokens")
                or 0
            ),
            reasoning_tokens=int(
                raw.get("reasoning_tokens")
                or (raw.get("output_token_details") or {}).get("reasoning_tokens")
                or 0
            ),
            cache_read_tokens=int(
                raw.get("cache_read_tokens")
                or raw.get("input_token_details", {}).get("cache_read")
                or 0
            ),
        )
    return None


def merge_usage(a: TokenUsage | None, b: TokenUsage | None) -> TokenUsage | None:
    if a is None:
        return b
    if b is None:
        return a
    return TokenUsage(
        input_tokens=a.input_tokens + b.input_tokens,
        output_tokens=a.output_tokens + b.output_tokens,
        reasoning_tokens=a.reasoning_tokens + b.reasoning_tokens,
        cache_read_tokens=a.cache_read_tokens + b.cache_read_tokens,
    )


def estimate_cost_usd(model_id: str | None, usage: TokenUsage | None) -> float | None:
    if not usage or not model_id:
        return None
    model = model_id.split(":", 1)[-1]
    prices = None
    for prefix, pair in _PRICE_PER_MTOK.items():
        if model.startswith(prefix):
            prices = pair
            break
    if prices is None:
        return None
    inp, out = prices
    return round(
        (usage.input_tokens * inp + usage.output_tokens * out) / 1_000_000,
        6,
    )
