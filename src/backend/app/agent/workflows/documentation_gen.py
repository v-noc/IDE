from app.agent.workflows.base import BaseWorkflow
from app.agent.context.graph_traversal import GraphTraversal


class DocumentationGeneratorWorkflow(BaseWorkflow):
    name = "documentation_generator"
    description = "Generate documentation for code elements recursively"

    def __init__(self, graph: GraphTraversal, llm_factory):
        self.graph = graph
        self.llm_factory = llm_factory

    async def run(self, node_id: str, direction: str = "down", mode: str = "documentation", max_depth: int = 5):
        pass
