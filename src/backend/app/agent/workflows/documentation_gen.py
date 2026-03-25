# app/agent/workflows/documentation_gen.py

from __future__ import annotations

from typing import Any

from app.agent.context.graph_traversal import GraphTraversal
from app.agent.runner.task_context import TaskContext
from app.agent.workflows.description_gen import (
    DescriptionGeneratorWorkflow,
    _NODE_TYPES,
)
from app.agent.workflows.node_persistence import NodePersistence
from app.agent.workflows.traversal_helpers import ordered_nodes


class DocumentationGeneratorWorkflow(DescriptionGeneratorWorkflow):
    """Recursive doc generation; persisted as markdown with empty ``data`` (see ``NodePersistence``)."""

    name = "documentation_generator"
    description = (
        "Generate documentation recursively from a tree"
    )

    def __init__(
        self,
        graph: GraphTraversal | None = None,
        llm_factory=None,
    ):
        super().__init__(graph=graph, llm_factory=llm_factory)

    async def execute(self, ctx: TaskContext, **kwargs) -> dict:
        self._read_llm_options(kwargs)
        kwargs.pop("description_mode", None)
        documentation_mode = kwargs.pop(
            "documentation_mode", "upsert"
        )

        node_id = kwargs.get("node_id")
        direction = kwargs.get("direction", "down")
        max_depth = kwargs.get("max_depth", 5)

        ctx.update_progress(0.0, "Building tree...")

        roots = await self.graph.build_tree(
            node_id=node_id,
            node_types=_NODE_TYPES,
            max_depth=max_depth,
        )
        nodes = ordered_nodes(roots, direction)

        if not nodes:
            return {
                "processed": 0,
                "documentation_results": {},
                "upserted_document_ids": [],
            }

        persistence = NodePersistence(self.graph)

        if documentation_mode == "insert_only":
            filtered = []
            for n in nodes:
                nid = getattr(n, "id", None)
                if nid and not await persistence.check_document_exists(
                    nid
                ):
                    filtered.append(n)
            nodes = filtered

        if not nodes:
            return {
                "processed": 0,
                "documentation_results": {},
                "upserted_document_ids": [],
            }

        doc_values: dict[str, str] = {}
        processed_nodes: dict[str, Any] = {}

        for index, tree_node in enumerate(nodes):
            nid = getattr(tree_node, "id", None)
            if not nid:
                continue

            node_doc = self._tree_node_to_prompt_doc(tree_node)
            node_doc["code_content_data"] = (
                await self.graph.get_code_content(nid)
            )
            node_name = node_doc.get("name", nid)

            st = ctx.subtask(
                name=node_name,
                subtask_id=nid,
                touched_node_ids=[nid],
            )
            st.start(f"Generating documentation for {node_name}")

            # Use freshly generated docs for child context
            child_docs = self._gather_child_values(
                tree_node, doc_values, attr="description"
            )
            # Use tree descriptions for child descriptions
            child_descs = self._gather_child_values(
                tree_node, {}, attr="description"
            )

            prompt = self._build_documentation_prompt(
                node_doc=node_doc,
                node_description=(
                    getattr(tree_node, "description", "") or ""
                ),
                child_documentations=child_docs,
                child_descriptions=child_descs,
            )

            try:
                text = await self._invoke_llm(prompt)
                doc_values[nid] = text
                processed_nodes[nid] = tree_node
                st.complete(f"Done: {node_name}")
            except Exception as exc:
                st.fail(str(exc))
                raise

        upserted_ids = (
            await persistence.flush_documentation_batch(
                doc_values, processed_nodes
            )
        )

        return {
            "processed": len(doc_values),
            "direction": direction,
            "documentation_results": doc_values,
            "upserted_document_ids": upserted_ids,
        }

    def _build_documentation_prompt(
        self,
        *,
        node_doc: dict,
        node_description: str,
        child_documentations: list[str],
        child_descriptions: list[str],
    ) -> str:
        child_doc_ctx = (
            "\n".join(f"- {d}" for d in child_documentations)
            if child_documentations
            else "None"
        )
        child_desc_ctx = (
            "\n".join(f"- {d}" for d in child_descriptions)
            if child_descriptions
            else "None"
        )
        code_ctx = (
            self._extract_code_context(node_doc)
            or "No direct code content found."
        )
        return (
            "Task: documentation\n"
            "Write practical technical documentation for this "
            "node.\n"
            "Use node description and child outputs to keep "
            "hierarchy-consistent docs.\n\n"
            f"Node id: {node_doc.get('@id')}\n"
            f"Node type: {node_doc.get('@type')}\n"
            f"Node name: {node_doc.get('name')}\n"
            f"Node description: {node_description}\n\n"
            f"Code context:\n{code_ctx}\n\n"
            f"Child documentations:\n{child_doc_ctx}\n\n"
            f"Child descriptions:\n{child_desc_ctx}\n"
        )
