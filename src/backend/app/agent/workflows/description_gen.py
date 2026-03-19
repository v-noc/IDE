from collections import deque
from typing import Any

from langchain_core.messages import HumanMessage

from app.db.async_terminus_client import WOQLQuery as WQ
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
        node_id: str | None = None,
        # "up" (leaf -> parent) | "down" (parent -> leaf)
        direction: str = "down",
        max_depth: int = 5,
        task_status: TaskStatus | None = None,
        **kwargs,
    ):
        if self.graph is None:
            raise ValueError(
                "GraphTraversal is required for description workflow."
            )
        if self.llm_factory is None:
            raise ValueError(
                "LLM factory is required for description workflow.")
        if direction not in {"up", "down"}:
            raise ValueError(f"Invalid direction: {direction}")

        roots = await self.graph.build_tree(
            node_id=node_id,
            node_types=["FileSchema", "FunctionSchema",
                        "ClassSchema", "FolderSchema"],
            max_depth=max_depth,
        )
        execution_nodes = self._ordered_nodes(roots=roots, direction=direction)

        total = len(execution_nodes)
        if total == 0:
            return {"processed": 0, "results": {}}

        generated_descriptions: dict[str, str] = {}
        node_updates: dict[str, Any] = {}

        for index, tree_node in enumerate(execution_nodes):
            node_id = getattr(tree_node, "id", None)
            if not node_id:
                continue

            node_doc = self._tree_node_to_prompt_doc(tree_node)
            node_doc["code_content_data"] = await self.graph.get_code_content(node_id)

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

            node_updates[node_id] = tree_node.model_copy(
                update={"description": generated_description}
            )

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
            child_description = getattr(child, "description", None)
            if not child_description:
                continue
            values.append(child_description)
        return values

    def _tree_node_to_prompt_doc(self, tree_node: Any) -> dict:
        node_type = f"{tree_node.__class__.__name__.replace('TreeNode', 'Schema')}"
        return {
            "@id": getattr(tree_node, "id", None),
            "@type": node_type,
            "name": getattr(tree_node, "name", ""),
            "description": getattr(tree_node, "description", ""),
        }

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
        code_context = (
            self._extract_code_context(node_doc)
            or "No direct code content found."
        )

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
        node_updates: dict[str, Any],
    ) -> None:
        if not self.graph:
            return

        if not node_updates:
            return

        client = self.graph.repos.client
        if not client:
            return

        for node in node_updates.values():
            node_id = getattr(node, "id", None)
            if not node_id:
                continue

            queries = []
            if hasattr(node, "description"):
                queries.extend(
                    [
                        WQ().opt(
                            WQ()
                            .triple(node_id, "description", "v:old_description")
                            .delete_triple(
                                node_id, "description", "v:old_description"
                            )
                        ),
                        WQ().add_triple(
                            node_id,
                            "description",
                            WQ().string(getattr(node, "description", "") or ""),
                        ),
                    ]
                )

            if hasattr(node, "documents"):
                for document_id in set(getattr(node, "documents") or set()):
                    queries.append(
                        WQ().opt(
                            WQ().add_triple(node_id, "documents", document_id)
                        )
                    )

            if queries:
                await client.query(
                    WQ().woql_and(*queries),
                    commit_msg=f"Workflow: update node {node_id}",
                )
