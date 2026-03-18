from abc import ABC, abstractmethod
from typing import Any
from app.agent.tools.tool_card import ToolCard


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @abstractmethod
    def get_card(self) -> ToolCard:
        """Return the tool's self-describing metadata."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Run the tool with validated inputs. Returns structured output."""
        ...

    def validate_inputs(self, **kwargs) -> dict:
        """Optional input validation hook. Override to add custom checks."""
        return kwargs
