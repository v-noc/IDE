import pytest

from app.agent.prompts import agent as _agent  # noqa: F401
from app.agent.prompts.registry import get_prompt_registry
from app.agent.prompts.shared import AGENT_PERSONA, GLOSSARY


def test_agent_system_renders_with_slots():
    registry = get_prompt_registry()
    text = registry.render(
        "agent.system",
        persona=AGENT_PERSONA,
        glossary=GLOSSARY,
        project_block='<project name="demo">A demo.</project>',
        tools="(no tools registered)",
    )
    assert "<project name=\"demo\">" in text
    assert "never invent" in text.lower() or "never guess" in text.lower()
    assert registry.version("agent.system") == "1"


def test_agent_system_rejects_missing_slot():
    registry = get_prompt_registry()
    with pytest.raises(ValueError, match="slot mismatch"):
        registry.render(
            "agent.system",
            persona=AGENT_PERSONA,
            glossary=GLOSSARY,
            project_block="<project/>",
        )
