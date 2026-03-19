from collections import deque
from typing import Any

from langchain_core.messages import HumanMessage

from app.agent.workflows.base import BaseWorkflow
from app.agent.context.graph_traversal import GraphTraversal
from app.agent.models.task_status import TaskStatus


class DescriptionGeneratorWorkflow(BaseWorkflow):
    name = "description_generator"
    description = "Generate descriptions recursively from a tree"

    def __init__(self, graph: GraphTraversal | None = None, llm_factory=None):
        self.graph = graph
        self.llm_factory = llm_factory

    async def run(
        self,
        node_id: str,
        direction: str = "down",   # "up" (leaf -> parent) | "down" (parent -> leaf)
        max_depth: int = 5,
        task_status: TaskStatus | None = None,
        **kwargs,
    ):
        if self.graph is None:
            raise ValueError("GraphTraversal is required for description workflow.")
        if self.llm_factory is None:
            raise ValueError("LLM factory is required for description workflow.")
        if direction not in {"up", "down"}:
            raise ValueError(f"Invalid direction: {direction}")

        roots = await self.graph.build_tree(node_id=node_id, max_depth=max_depth)
        execution_nodes = self._ordered_nodes(roots=roots, direction=direction)

        total = len(execution_nodes)
        if total == 0:
            return {"processed": 0, "results": {}}

        generated_descriptions: dict[str, str] = {}
        node_updates: dict[str, dict] = {}

        for index, tree_node in enumerate(execution_nodes):
            node_id = getattr(tree_node, "id", None)
            if not node_id:
                continue

            node_doc = await self.graph.get_node_with_code(node_id)
            if not node_doc:
                continue

            child_descriptions = self._child_values(
                tree_node=tree_node,
                generated_values=generated_descriptions,
            )
            prompt = self._build_description_prompt(
                node_doc=node_doc,
                child_descriptions=child_descriptions,
            )
            generated_description = await self._invoke_llm(prompt)
            generated_descriptions[node_id] = generated_description

            updated_node_doc = dict(node_updates.get(node_id, node_doc))
            updated_node_doc["description"] = generated_description
            node_updates[node_id] = updated_node_doc

            if task_status:
                task_status.progress = (index + 1) / total
                task_status.progress_message = (
                    f"Generated description: {node_doc.get('name', node_id)}"
                )

        await self._flush_node_updates(
            node_updates=node_updates
        )

        return {
            "processed": len(generated_descriptions),
            "direction": direction,
            "description_results": generated_descriptions,
        }

    def _ordered_nodes(self, roots: list[Any], direction: str) -> list[Any]:
        levels = self._collect_levels(roots)
        if direction == "up":
            levels = list(reversed(levels))
        return [node for level in levels for node in level]

    def _collect_levels(self, roots: list[Any]) -> list[list[Any]]:
        if not roots:
            return []

        levels: list[list[Any]] = []
        queue: deque[tuple[Any, int]] = deque()
        visited: set[str] = set()

        for root in roots:
            root_id = getattr(root, "id", None)
            if not root_id or root_id in visited:
                continue
            visited.add(root_id)
            queue.append((root, 0))

        while queue:
            node, depth = queue.popleft()
            while len(levels) <= depth:
                levels.append([])
            levels[depth].append(node)

            for child in getattr(node, "children", []) or []:
                child_id = getattr(child, "id", None)
                if not child_id or child_id in visited:
                    continue
                visited.add(child_id)
                queue.append((child, depth + 1))

        return levels

    def _child_values(
        self,
        tree_node: Any,
        generated_values: dict[str, str],
    ) -> list[str]:
        values: list[str] = []
        for child in getattr(tree_node, "children", []) or []:
            child_id = getattr(child, "id", None)
            if not child_id:
                continue
            child_value = generated_values.get(child_id)
            if child_value:
                values.append(child_value)
        return values

    async def _invoke_llm(self, prompt: str) -> str:
        llm = self.llm_factory.create(model="gpt-4o-mini")
        response = await llm.invoke([HumanMessage(content=prompt)])
        content = getattr(response, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(text)
            return "\n".join(parts).strip()
        return str(content).strip()

    def _extract_code_context(self, node_doc: dict) -> str:
        node_type = (node_doc.get("@type") or "").replace("Schema", "")
        if node_type not in {"File", "Function", "Class"}:
            return ""
        code_content = node_doc.get("code_content_data")
        if isinstance(code_content, str) and code_content.strip():
            return code_content
        return ""

    def _build_description_prompt(
        self,
        *,
        node_doc: dict,
        child_descriptions: list[str],
    ) -> str:
        child_context = (
            "\n".join([f"- {item}" for item in child_descriptions])
            if child_descriptions else "None"
        )
        code_context = self._extract_code_context(node_doc) or "No direct code content found."

        return (
            "Task: description\n"
            "Write a concise technical description of this node.\n"
            "Use child descriptions for context and avoid repetition.\n\n"
            f"Node id: {node_doc.get('@id')}\n"
            f"Node type: {node_doc.get('@type')}\n"
            f"Node name: {node_doc.get('name')}\n"
            f"Current description: {node_doc.get('description', '')}\n\n"
            f"Code context:\n{code_context}\n\n"
            f"Child descriptions:\n{child_context}\n"
        )

    async def _flush_node_updates(
        self,
        *,
        node_updates: dict[str, dict],
    ) -> None:
        if not self.graph or not self.graph.repos.client:
            return

        if node_updates:
            await self.graph.repos.client.update_document(
                list(node_updates.values()),
                commit_msg=f"Workflow: update {len(node_updates)} node descriptions",
            )
