import pytest

from app.agent.llm.structured import structured_call
from app.walkthrough.schemas import IntroOut


@pytest.mark.asyncio
async def test_structured_call_fake_intro():
    result, errors = await structured_call(
        "intro",
        IntroOut,
        "system",
        "### node\ncharge — payments.py\nCharges a card.",
    )
    assert result is not None
    assert "charge" in result.intro.lower()
    assert errors == []


@pytest.mark.asyncio
async def test_structured_call_retries_then_succeeds():
    from app.agent.llm.fake import FakeLLM
    from app.agent.llm import structured as structured_module

    original = structured_module.make_llm

    def fake_factory(call_type: str, **_kwargs) -> FakeLLM:
        return FakeLLM(call_type, fail_first_attempts=1)

    structured_module.make_llm = fake_factory
    try:
        result, errors = await structured_call(
            "intro",
            IntroOut,
            "system",
            "### node\nrefund\nRefunds.",
        )
        assert result is not None
        assert len(errors) >= 1
    finally:
        structured_module.make_llm = original
