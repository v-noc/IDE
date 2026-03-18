from app.agent.tools.base import BaseTool


class ToolRegistry:
    """Discover, register, enable/disable tools at runtime."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        card = tool.get_card()
        self._tools[card.name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def list_cards(self, enabled_only: bool = True) -> list[ToolCard]:
        """Return tool cards (useful for feeding to the LLM planner)."""
        return [t.get_card() for t in self._tools.values()]

    def auto_discover(self, package_path: str = "app.agent.tools") -> None:
        """Walk subpackages, import any BaseTool subclass, register it."""
        ...
