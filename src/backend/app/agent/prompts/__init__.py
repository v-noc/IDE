from app.agent.prompts import agent as _agent  # noqa: F401 — register on import
from app.agent.prompts.registry import (
    PromptDef,
    PromptRegistry,
    get_prompt_registry,
    register_prompt,
)
from app.agent.prompts.shared import AGENT_PERSONA, GLOSSARY

__all__ = [
    "AGENT_PERSONA",
    "GLOSSARY",
    "PromptDef",
    "PromptRegistry",
    "get_prompt_registry",
    "register_prompt",
]
