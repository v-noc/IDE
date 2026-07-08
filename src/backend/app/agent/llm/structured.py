from __future__ import annotations

from typing import Callable, TypeVar

from pydantic import BaseModel

from app.agent.llm.fake import FakeLLM
from app.agent.llm.providers import resolve_provider
from app.config.settings import get_settings

T = TypeVar("T", bound=BaseModel)

CALL_PARAMS = {
    "intro": {"temperature": 0.5, "max_tokens": 300},
    "block_plan": {"temperature": 0.2, "max_tokens": 400},
    "block_text": {"temperature": 0.5, "max_tokens": 350},
}


def make_llm(call_type: str) -> FakeLLM:
    spec = resolve_provider()
    if spec.name == "fake":
        return FakeLLM(call_type=call_type)
    raise NotImplementedError(
        f"Provider '{spec.name}' is not wired yet — set WALKTHROUGH_LLM_PROVIDER=fake",
    )


async def structured_call(
    call_type: str,
    schema: type[T],
    system: str,
    user: str,
    validate: Callable[[T], list[str]] | None = None,
) -> tuple[T | None, list[str]]:
    validate = validate or (lambda _: [])
    error_log: list[str] = []
    prompt = user
    llm = make_llm(call_type)

    for attempt in range(2):
        try:
            result = await llm.invoke_structured(schema, system, prompt)
            issues = validate(result)
            if issues:
                error_log.extend(issues)
                prompt = (
                    f"{user}\n\nValidation errors from the previous attempt:\n"
                    + "\n".join(f"- {issue}" for issue in issues)
                )
                continue
            return result, error_log
        except Exception as exc:
            error_log.append(f"{call_type} attempt {attempt + 1}: {exc}")

    return None, error_log
