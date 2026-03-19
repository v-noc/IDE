from app.agent.context.graph_traversal import GraphTraversal
from app.agent.workflows.description_gen import DescriptionGeneratorWorkflow
from app.agent.models.task_status import TaskStatus
from app.core.model.schemas import DocumentSchema
from datetime import datetime, timezone
from terminusdb_client.woqlquery.woql_query import Doc
from app.db.async_terminus_client import WOQLQuery as WQ


class DocumentationGeneratorWorkflow(DescriptionGeneratorWorkflow):
    name = "documentation_generator"
    description = "Generate documentation recursively from a tree"

    def __init__(self, graph: GraphTraversal | None = None, llm_factory=None):
        super().__init__(graph=graph, llm_factory=llm_factory)

    async def run(
        self,
        node_id: str | None = None,
        direction: str = "down",
        max_depth: int = 5,
        task_status: TaskStatus | None = None,
        **kwargs,
    ):
        # Documentation starts only after description phase finishes.
        if task_status:
            task_status.progress = 0.0
            task_status.progress_message = (
                "Generating descriptions before documentation..."
            )

        if self.graph is None:
            raise ValueError(
                "GraphTraversal is required for documentation workflow."
            )

        roots = await self.graph.build_tree(
            node_id=node_id,
            node_types=["FileSchema", "FunctionSchema",
                        "ClassSchema", "FolderSchema"],
            max_depth=max_depth,
        )
        execution_nodes = self._ordered_nodes(roots=roots, direction=direction)
        if not execution_nodes:
            return {
                "processed": 0,
                "documentation_results": {},
                "upserted_document_ids": [],
            }

        documentation_values: dict[str, str] = {}
        processed_nodes: dict[str, object] = {}

        total = len(execution_nodes)
        for index, tree_node in enumerate(execution_nodes):
            current_node_id = getattr(tree_node, "id", None)
            if not current_node_id:
                continue

            node_doc = self._tree_node_to_prompt_doc(tree_node)
            node_doc["code_content_data"] = await self.graph.get_code_content(
                current_node_id
            )

            child_documentations = self._child_values(
                tree_node=tree_node,
                generated_values=documentation_values,
            )
            child_descriptions = self._child_values(
                tree_node=tree_node,
                generated_values=tree_node.description,
            )

            prompt = self._build_documentation_prompt(
                node_doc=node_doc,
                node_description=tree_node.description,
                child_documentations=child_documentations,
                child_descriptions=child_descriptions,
            )
            documentation_values[current_node_id] = await self._invoke_llm(
                prompt
            )
            processed_nodes[current_node_id] = tree_node

            if task_status:
                phase_progress = (index + 1) / total
                task_status.progress = 0.5 + (phase_progress * 0.5)
                task_status.progress_message = (
                    "Generated documentation: "
                    f"{node_doc.get('name', current_node_id)}"
                )

        upserted_doc_ids = await self._flush_documentation_batch(
            documentation_values,
            processed_nodes,
        )
        return {
            "processed": len(documentation_values),
            "direction": direction,

            "documentation_results": documentation_values,
            "upserted_document_ids": upserted_doc_ids,
        }

    def _build_documentation_prompt(
        self,
        *,
        node_doc: dict,
        node_description: str,
        child_documentations: list[str],
        child_descriptions: list[str],
    ) -> str:
        child_doc_context = (
            "\n".join([f"- {item}" for item in child_documentations])
            if child_documentations else "None"
        )
        child_desc_context = (
            "\n".join([f"- {item}" for item in child_descriptions])
            if child_descriptions else "None"
        )
        code_context = (
            self._extract_code_context(node_doc)
            or "No direct code content found."
        )

        return (
            "Task: documentation\n"
            "Write practical technical documentation for this node.\n"
            "Use node description and child outputs to keep "
            "hierarchy-consistent docs.\n\n"
            f"Node id: {node_doc.get('@id')}\n"
            f"Node type: {node_doc.get('@type')}\n"
            f"Node name: {node_doc.get('name')}\n"
            f"Node description: {node_description}\n\n"
            f"Code context:\n{code_context}\n\n"
            f"Child documentations:\n{child_doc_context}\n\n"
            f"Child descriptions:\n{child_desc_context}\n"
        )

    @staticmethod
    def _documentation_doc_id(node_id: str) -> str:
        safe = node_id.replace("/", "_").replace(":", "_")
        return f"DocumentSchema/{safe}_workflow_documentation"

    async def _flush_documentation_batch(
        self,
        documentation_values: dict[str, str],
        processed_nodes: dict[str, object],
    ) -> list[str]:
        if (
            not self.graph
            or not self.graph.repos.client
            or not documentation_values
        ):
            return []

        client = self.graph.repos.client
        now = datetime.now(timezone.utc)
        doc_ids = [
            self._documentation_doc_id(node_id)
            for node_id in documentation_values
        ]

        existing_docs: dict[str, dict] = {}
        try:
            existing = await client.get_documents(doc_ids)
            existing_docs = {doc.get("@id"): doc for doc in existing}
        except Exception:
            existing_docs = {}

        document_queries = []
        node_link_queries = []

        for node_id, content in documentation_values.items():
            doc_id = self._documentation_doc_id(node_id)
            existing_doc = existing_docs.get(doc_id, {})
            created_at = existing_doc.get("created_at", now)

            document_schema = DocumentSchema(
                _id=doc_id,
                name=f"workflow_doc:{node_id}",
                description="Generated by documentation workflow.",
                data=content,
                created_at=created_at,
                updated_at=now,
            )
            document_raw = document_schema._obj_to_dict()[0]
            document_queries.append(
                WQ().insert_document(Doc(document_raw)),
            )

            tree_node = processed_nodes.get(node_id)
            if tree_node is None:
                continue

            tree_node_id = getattr(tree_node, "id", None)
            if not tree_node_id:
                continue
            node_link_queries.append(
                WQ().opt(WQ().add_triple(tree_node_id, "documents", doc_id))
            )

        if document_queries:
            await client.query(
                WQ().woql_and(*document_queries),
                commit_msg=(
                    f"Workflow: upsert {len(document_queries)} "
                    "generated documents"
                ),
            )
        if node_link_queries:
            await client.query(
                WQ().woql_and(*node_link_queries),
                commit_msg=(
                    f"Workflow: link {len(node_link_queries)} documents to nodes"
                ),
            )

        return doc_ids
