# app/agent/workflows/description_gen.py

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.runner.task_context import TaskContext
from app.agent.workflows.base import BaseWorkflow
from app.agent.workflows.node_persistence import NodePersistence
from app.agent.workflows.traversal_helpers import ordered_nodes

_NODE_TYPES = [
    "FileSchema",
    "FunctionSchema",
    "ClassSchema",
    "FolderSchema",
]


class DescriptionGeneratorWorkflow(BaseWorkflow):
    name = "description_generator"
    description = "Generate descriptions recursively from a tree"

    def __init__(
        self,
        graph: GraphTraversal | None = None,
        llm_factory=None,
    ):
        self.graph = graph
        self.llm_factory = llm_factory

    async def validate(self, **kwargs) -> None:
        if self.graph is None:
            raise ValueError(
                "GraphTraversal is required for description workflow."
            )
        if self.llm_factory is None:
            raise ValueError(
                "LLM factory is required for description workflow."
            )
        direction = kwargs.get("direction", "down")
        if direction not in {"up", "down"}:
            raise ValueError(f"Invalid direction: {direction}")

    async def execute(self, ctx: TaskContext, **kwargs) -> dict:
        self._read_llm_options(kwargs)
        node_id = kwargs.get("node_id")
        direction = kwargs.get("direction", "down")
        max_depth = kwargs.get("max_depth", 5)
        description_mode = kwargs.pop("description_mode", "always")

        ctx.update_progress(0.0, "Building tree...")

        roots = await self.graph.build_tree(
            node_id=node_id,
            node_types=_NODE_TYPES,
            max_depth=max_depth,
        )
        nodes = ordered_nodes(roots, direction)

        if description_mode == "skip_if_present":
            nodes = [
                n
                for n in nodes
                if not (
                    getattr(n, "description", None) or ""
                ).strip()
            ]

        if not nodes:
            return {"processed": 0, "results": {}}

        generated: dict[str, str] = {}
        node_updates: dict[str, Any] = {}

        for index, tree_node in enumerate(nodes):
            nid = getattr(tree_node, "id", None)
            if not nid:
                continue

            node_doc = self._tree_node_to_prompt_doc(tree_node)
            node_doc["code_content_data"] = (
                await self.graph.get_code_content(nid)
            )

            node_name = node_doc.get("name", nid)

            # -- register subtask --
            st = ctx.subtask(
                name=node_name,
                subtask_id=nid,
                touched_node_ids=[nid],
            )
            st.start(f"Generating description for {node_name}")

            child_descs = self._gather_child_values(
                tree_node, generated, attr="description"
            )
            prompt = self._build_description_prompt(
                node_doc=node_doc,
                child_descriptions=child_descs,
            )

            try:
                text = await self._invoke_llm(prompt)

                generated[nid] = text
                node_updates[nid] = tree_node.model_copy(
                    update={"description": text}
                )
                st.complete(f"Done: {node_name}")
            except Exception as exc:
                st.fail(str(exc))
                raise

        persistence = NodePersistence(self.graph)
        await persistence.flush_descriptions(node_updates)

        return {
            "processed": len(generated),
            "direction": direction,
            "description_results": generated,
        }

    # -- shared helpers ---------------------------------------------------

    def _read_llm_options(self, kwargs: dict) -> None:
        self._invoke_model = (
            kwargs.pop("model", None) or "gpt-4o-mini"
        )
        self._invoke_provider = kwargs.pop("provider", None)

    @staticmethod
    def _tree_node_to_prompt_doc(tree_node: Any) -> dict:
        node_type = tree_node.__class__.__name__.replace(
            "TreeNode", "Schema"
        )
        return {
            "@id": getattr(tree_node, "id", None),
            "@type": node_type,
            "name": getattr(tree_node, "name", ""),
            "description": getattr(tree_node, "description", ""),
        }

    @staticmethod
    def _gather_child_values(
        tree_node: Any,
        generated_values: dict[str, str],
        attr: str = "description",
    ) -> list[str]:
        """
        Collect child values, preferring freshly generated
        values over the tree node's original attribute.
        """
        values: list[str] = []
        for child in getattr(tree_node, "children", []) or []:
            child_id = getattr(child, "id", None)
            if not child_id:
                continue
            # Freshly generated wins
            val = generated_values.get(child_id)
            if not val:
                val = getattr(child, attr, None)
            if val and isinstance(val, str) and val.strip():
                values.append(val)
        return values

    @staticmethod
    def _extract_code_context(node_doc: dict) -> str:
        node_type = (
            (node_doc.get("@type") or "").replace("Schema", "")
        )
        if node_type not in {"File", "Function", "Class"}:
            return ""
        code = node_doc.get("code_content_data")
        if isinstance(code, str) and code.strip():
            return code
        return ""

    def _build_description_prompt(
        self,
        *,
        node_doc: dict,
        child_descriptions: list[str],
    ) -> str:
        child_ctx = (
            "\n".join(f"- {d}" for d in child_descriptions)
            if child_descriptions
            else "None"
        )
        code_ctx = (
            self._extract_code_context(node_doc)
            or "No direct code content found."
        )
        return (
            "Task: description\n"
            "Write a concise technical description of this "
            "node.\n"
            "Use child descriptions for context and avoid "
            "repetition.\n\n"
            f"Node id: {node_doc.get('@id')}\n"
            f"Node type: {node_doc.get('@type')}\n"
            f"Node name: {node_doc.get('name')}\n"
            f"Current description: "
            f"{node_doc.get('description', '')}\n\n"
            f"Code context:\n{code_ctx}\n\n"
            f"Child descriptions:\n{child_ctx}\n"
        )

    async def _invoke_llm(self, prompt: str) -> str:

        model = (
            getattr(self, "_invoke_model", None) or "gpt-4o-mini"
        )
        provider = getattr(self, "_invoke_provider", None)
        llm = self.llm_factory.create(
            provider=provider, model=model
        )
        response = await llm.invoke(
            [HumanMessage(content=prompt)]
        )
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
