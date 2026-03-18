from agent.workflows.base import BaseWorkflow
from app.agent.context.graph_traversal import GraphTraversal
from app.agent.llm.factory import create_llm
from app.agent.models.task_status import TaskStatus


class DescriptionGeneratorWorkflow(BaseWorkflow):
    name = "description_generator"
    description = "Generate descriptions for code elements recursively"

    def __init__(self, graph: GraphTraversal, llm_factory):
        self.graph = graph
        self.llm_factory = llm_factory

    async def run(
        self,
        node_id: str,
        direction: str = "down",           # "up" | "down"
        mode: str = "description",         # "description" | "documentation" | "both"
        max_depth: int = 5,
        task_status: TaskStatus | None = None,
    ):
        if direction == "down":
            nodes = await self.graph.traverse_down(node_id, max_depth)
            nodes = self._sort_leaf_first(nodes)
        else:
            nodes = await self.graph.traverse_up(node_id, max_depth)

        total = len(nodes)
        results = {}

        for i, node in enumerate(nodes):
            # 2. Gather context
            code = await self.graph.get_node_with_code(node["id"])
            child_descriptions = [
                results[cid] for cid in node.get("children", [])
                if cid in results
            ]

            # 3. Generate
            if mode in ("description", "both"):
                desc = await self._generate_description(node, code, child_descriptions)
                results[node["id"]] = desc
                # TODO: persist to TerminusDB

            if mode in ("documentation", "both"):
                doc = await self._generate_documentation(node, code, child_descriptions)
                # TODO: persist as DocumentSchema

            # 4. Progress
            if task_status:
                task_status.progress = (i + 1) / total
                task_status.progress_message = f"Processed {node['name']}"

        return results

    async def _generate_description(self, node, code, child_descriptions) -> str:
        llm = self.llm_factory.create(model="gpt-4o-mini")
        prompt = self._build_description_prompt(node, code, child_descriptions)
        return await llm.ainvoke(prompt)

    async def _generate_documentation(self, node, code, child_descriptions) -> str:
        llm = self.llm_factory.create(model="gpt-4o-mini")
        prompt = self._build_documentation_prompt(
            node, code, child_descriptions)
        return await llm.ainvoke(prompt)
