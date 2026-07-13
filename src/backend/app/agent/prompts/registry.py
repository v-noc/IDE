from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.config.settings import get_settings


class PromptDef(BaseModel):
    name: str
    version: str
    template: str
    slots: list[str] = Field(default_factory=list)


class PromptRegistry:
    def __init__(self) -> None:
        self._defs: dict[str, PromptDef] = {}

    def register(self, prompt: PromptDef) -> None:
        self._defs[prompt.name] = prompt

    def get(self, name: str) -> PromptDef:
        if name not in self._defs:
            raise KeyError(f"Unknown prompt: {name}")
        return self._defs[name]

    def version(self, name: str) -> str:
        return self.get(name).version

    def render(self, name: str, **slots: str) -> str:
        prompt = self.get(name)
        expected = set(prompt.slots)
        given = set(slots)
        missing = expected - given
        extra = given - expected
        if missing or extra:
            raise ValueError(
                f"Prompt {name!r} slot mismatch: "
                f"missing={sorted(missing)} extra={sorted(extra)}",
            )
        return prompt.template.format(**slots)

    def names(self) -> list[str]:
        return sorted(self._defs)


_REGISTRY = PromptRegistry()


def get_prompt_registry() -> PromptRegistry:
    return _REGISTRY


def register_prompt(prompt: PromptDef) -> None:
    _REGISTRY.register(prompt)


def _apply_overrides(registry: PromptRegistry) -> None:
    settings = get_settings()
    override_dir = settings.PROMPT_OVERRIDE_DIR
    if not override_dir:
        return
    root = Path(override_dir)
    if not root.is_dir():
        return
    for path in root.glob("*.md"):
        name = path.stem  # e.g. agent.system
        text = path.read_text(encoding="utf-8")
        version = "override"
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                front = parts[1]
                body = parts[2].lstrip("\n")
                for line in front.splitlines():
                    if line.strip().startswith("version:"):
                        version = line.split(":", 1)[1].strip().strip('"')
        existing = registry.get(name) if name in registry.names() else None
        slots = existing.slots if existing else []
        registry.register(
            PromptDef(name=name, version=version, template=body, slots=slots),
        )
