from app.agent.context.graph_traversal import GraphTraversal
from app.agent.context.vectorlink_client import VectorLinkClient
from app.agent.context.token_tracker import TokenTracker


class ContextBUilder:
    """Assemble prompt context from multiple sources within a token budget."""

    def __init__(self,
                 graph: GraphTraversal,
                 vectorlink: VectorLinkClient,
                 budget: TokenTracker):
        self.graph = graph
        self.vectorlink = vectorlink
        self.budget = budget

    async def build_context(
        self,
        *,
        node_id: str | None = None,
        query: str | None = None,
        include_code: bool = False,
        traversal_direction: str = "down",
        traversal_depth: int = 2,
        vector_top_k: int = 5,
    ):
        """
        Build context by:
        1. Graph traversal from node_id (if provided)
        2. Vector search for query (if provided)
        3. Merge, deduplicate, rank by relevance
        4. Truncate to fit token budget
        5. Optionally attach code content
        """
        context_items = []

        # Step 1: Graph traversal
        if node_id:
            if traversal_direction == "down":
                nodes = await self.graph.traverse_down(node_id, traversal_depth)
            else:
                nodes = await self.graph.traverse_up(node_id, traversal_depth)
            context_items.extend(nodes)

        # Step 2: Vector search
        if query:
            results = await self.vectorlink.search(
                db="...",  # from ProjectUoW
                query=query,
                top_k=vector_top_k,
            )
            context_items.extend(results)

        # Step 3-5: Deduplicate, budget-check, enrich
        ...

        return context_items
