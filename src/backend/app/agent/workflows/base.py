from abc import ABC, abstractmethod
from typing import Any


class BaseWorkflow(ABC):
    """Abstract base for all deterministic workflows."""
    name: str
    description: str

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Run the workflow."""
        ...
