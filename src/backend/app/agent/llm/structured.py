from __future__ import annotations

from typing import Any, Callable, Protocol, TypeVar

from loguru import logger

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agent.llm.fake import FakeLLM
from app.agent.llm.providers import overrides_for, resolve_llm
from app.config.settings import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

# NO completion caps — deliberate (learned live, 2026-07-11). Reasoning models
# (gpt-5 family, o-series, GLM/Kimi thinking modes) spend max_tokens on hidden
# reasoning FIRST: observed reasoning_tokens=700 of a 700 cap, zero content,
# every intro failing "length limit reached". Length is steered by the prompts
# ("aim for 2-4 sentences" — a target, not a limit); cost is controlled by the
# tour-level estimate + visit cap, never by cutting a generation mid-thought.
CALL_PARAMS = {
    "intro": {"temperature": 0.5},
    "block_plan": {"temperature": 0.2},
    "block_text": {"temperature": 0.5},
}


class StructuredLLM(Protocol):
    async def invoke_structured(
        self,
        schema: type[T],
        system: str,
        user: str,
    ) -> T: ...


class ChatOpenAILLM:
    """OpenAI-compatible chat model with the FakeLLM invoke_structured surface."""

    def __init__(self, chat: ChatOpenAI):
        self._chat = chat

    async def invoke_structured(
        self,
        schema: type[T],
        system: str,
        user: str,
    ) -> T:
        runnable = self._chat.with_structured_output(
            schema,
            method="json_mode",
            include_raw=True,
        )
        result: Any = await runnable.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=user)],
        )

        if isinstance(result, dict):
            raw = result.get("raw")
            parsed = result.get("parsed")
            parsing_error = result.get("parsing_error")
        else:
            parsed = result
            parsing_error = None

        if parsing_error is not None:
            raise ValueError(f"structured output parse error: {parsing_error}")

        if parsed is None:
            raise ValueError("structured output returned no parsed result")

        return parsed  # type: ignore[return-value]


def make_llm(
    call_type: str,
    override: str | None = None,
    settings: Settings | None = None,
) -> StructuredLLM:
    settings = settings or get_settings()
    resolved = resolve_llm(override=override, settings=settings)

    if resolved.spec.name == "fake":
        return FakeLLM(call_type=call_type)

    if call_type not in CALL_PARAMS:
        raise ValueError(f"Unknown call_type: {call_type}")

    api_key = None
    if resolved.spec.api_key_field:
        api_key = getattr(settings, resolved.spec.api_key_field, None)
        if not api_key:
            raise ValueError(
                f"Missing {resolved.spec.api_key_field} for provider "
                f"{resolved.spec.name!r}",
            )

    base_url = resolved.spec.base_url
    if resolved.spec.name == "custom":
        base_url = settings.CUSTOM_LLM_BASE_URL
        if not base_url:
            raise ValueError("CUSTOM_LLM_BASE_URL is required for provider 'custom'")

    chat = ChatOpenAI(
        model=resolved.model,
        base_url=base_url,
        api_key=api_key,
        **CALL_PARAMS[call_type],
        **overrides_for(resolved.model),
        timeout=60,
        max_retries=1,
    )
    return ChatOpenAILLM(chat)


async def structured_call(
    call_type: str,
    schema: type[T],
    system: str,
    user: str,
    validate: Callable[[T], list[str]] | None = None,
    *,
    override: str | None = None,
) -> tuple[T | None, list[str]]:
    validate = validate or (lambda _: [])
    error_log: list[str] = []
    prompt = user
    llm = make_llm(call_type, override=override)

    for attempt in range(2):
        try:
            result = await llm.invoke_structured(schema, system, prompt)
            issues = validate(result)
            if issues:
                for issue in issues:
                    logger.warning(
                        "walkthrough llm validation failure call_type={} attempt={} error={}",
                        call_type,
                        attempt + 1,
                        issue,
                    )
                error_log.extend(issues)
                prompt = (
                    f"{user}\n\nValidation errors from the previous attempt:\n"
                    + "\n".join(f"- {issue}" for issue in issues)
                )
                continue
            return result, error_log
        except Exception as exc:
            logger.warning(
                "walkthrough llm failure call_type={} attempt={} error={}",
                call_type,
                attempt + 1,
                exc,
            )
            error_log.append(f"{call_type} attempt {attempt + 1}: {exc}")

    return None, error_log
