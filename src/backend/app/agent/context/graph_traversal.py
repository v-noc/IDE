from app.db.context import ProjectUoW
from app.core.model.nodes import BaseNode


class GraphTraversal:
    """Walk the TerminusDB graph up or down from a starting node."""

    def __init__(self, uow: ProjectUoW):
        self.repos = uow.get_project_repos()

    async def traverse_down(
        self,
        node_id: str,
        max_depth: int = 3,
        node_types: list[str] | None = None,
    ) -> list[dict]:
        """
        BFS/DFS downward from node_id.
        Returns a flat list of node dicts with depth metadata.
        Respects node_types filter (e.g. ["FunctionSchema", "ClassSchema"]).
        """
        ...

    async def traverse_up(
        self,
        node_id: str,
        max_depth: int = 3,
    ) -> list[dict]:
        """
        Walk upward via parent references.
        Useful for "what file/folder does this function belong to?"
        """
        ...

    async def get_siblings(self, node_id: str) -> list[dict]:
        """Get nodes at the same level (same parent)."""
        ...

    async def get_node_with_code(self, node_id: str) -> dict:
        """Fetch node + its CodeContentSchema content."""
        ...
