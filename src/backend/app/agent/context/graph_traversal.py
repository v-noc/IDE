from app.db.context import ProjectUoW
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.code_element_service import CodeElementService


class GraphTraversal:
    """Walk and shape project graph data for workflow execution."""

    EDGE_FIELDS = (
        "folder_children",
        "file_children",
        "class_children",
        "function_children",
        "call_children",
        "code_element_group",
        "call_group",
        "structure_group",
    )
    EDGE_PATTERN = "(" + "|".join(EDGE_FIELDS) + ")"

    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = uow.get_project_repos()
        self.code_service = CodeElementService(uow)

    def _extract_children(self, doc: dict) -> list[str]:
        children: list[str] = []
        for edge in self.EDGE_FIELDS:
            raw = doc.get(edge)
            if raw is None:
                continue
            if isinstance(raw, (list, set, tuple)):
                children.extend([str(item) for item in raw if item])
            else:
                children.append(str(raw))
        return list(set(children))

    @staticmethod
    def _normalize_type_name(type_name: str | None) -> str:
        if not type_name:
            return ""
        return type_name.replace("Schema", "")

    def _normalize_doc(self, doc: dict) -> dict:
        normalized = dict(doc)
        normalized["id"] = normalized.get("@id")
        normalized["type"] = normalized.get("@type")
        normalized["children"] = self._extract_children(doc)
        return normalized

    def _dedupe_nodes(self, nodes: list[dict]) -> list[dict]:
        unique: dict[str, dict] = {}
        for node in nodes:
            node_id = node.get("id") or node.get("@id")
            if not node_id:
                continue
            unique[node_id] = node
        return list(unique.values())

    # TODO: Make imporve type filtering
    async def traverse_down(
        self,
        node_id: str | None,
        max_depth: int = 5,
        node_types: list[str] | None = None,
    ) -> list[dict]:
        """
        Get all descendants from node_id and include the start node.
        Returns full node docs with normalized `id`, `type`, and `children`.
        """
        if not node_id:
            all_nodes, _ = await self.repos.project_repo.get_children(
                exclude_types=[])
            normalized_nodes = [
                self._normalize_doc(node.model_dump())
                for node in all_nodes
            ]
            return self._dedupe_nodes(normalized_nodes)

        pattern = "+" if max_depth <= 0 else f"{{1,{max_depth}}}"
        query = (
            WQ()
            .eq("v:start", node_id)
            .path("v:start", f"{self.EDGE_PATTERN}{pattern}", "v:child")
            .read_document("v:child", "v:child_doc")
        )

        allowed_types = None
        if node_types:
            allowed_types = {
                self._normalize_type_name(node_type) for node_type in node_types
            }

        nodes: list[dict] = []
        if self.repos.client:
            result = await self.repos.client.query(query)
            for row in result.get("bindings", []):
                doc = row.get("child_doc", {})
                if allowed_types:
                    doc_type = self._normalize_type_name(doc.get("@type"))
                    if doc_type not in allowed_types:
                        continue
                nodes.append(self._normalize_doc(doc))

            start_result = await self.repos.client.get_document(node_id)
            if start_result:
                nodes.append(self._normalize_doc(start_result))

        return self._dedupe_nodes(nodes)

    async def traverse_up(
        self,
        node_id: str,
        max_depth: int = 5,
    ) -> list[dict]:
        """
        Get all ancestors from node_id and include the start node.
        Returns full node docs with normalized `id`, `type`, and `children`.
        """
        pattern = "+" if max_depth <= 0 else f"{{1,{max_depth}}}"
        query = (
            WQ()
            .eq("v:start", node_id)
            .path("v:start", f"<{self.EDGE_PATTERN}{pattern}", "v:parent")
            .read_document("v:parent", "v:parent_doc")
        )

        nodes: list[dict] = []
        if self.repos.client:
            result = await self.repos.client.query(query)
            for row in result.get("bindings", []):
                doc = row.get("parent_doc", {})
                nodes.append(self._normalize_doc(doc))

            start_result = await self.repos.client.get_document(node_id)
            if start_result:
                nodes.append(self._normalize_doc(start_result))

        return self._dedupe_nodes(nodes)

    async def build_tree(self, node_id: str | None, node_types: list[str] | None = None, max_depth: int = 5):
        """Build nested tree nodes for subtree rooted at `node_id`."""
        nodes = await self.traverse_down(node_id=node_id, node_types=node_types, max_depth=max_depth)
        tree = TreeBuilder(base_nodes=nodes).build()
        return tree

    async def get_siblings(self, node_id: str) -> list[dict]:
        """Get nodes at the same level (same parent)."""
        parents = await self.traverse_up(node_id, max_depth=1)
        if not parents:
            return []

        parent_id = parents[0]["id"] if parents[0]["id"] != node_id else (
            parents[1]["id"] if len(parents) > 1 else None
        )
        if not parent_id:
            return []

        children = await self.traverse_down(parent_id, max_depth=1)
        return [c for c in children if c["id"] not in {node_id, parent_id}]

    async def get_node_with_code(self, node_id: str) -> dict:
        """Fetch node and hydrate code via CodeElementService.get_code."""
        if not self.repos.client:
            return {}

        doc = await self.repos.client.get_document(node_id)
        if not doc:
            return {}

        try:
            code_payload = await self.code_service.get_code(node_id)
            if code_payload and code_payload.get("code"):
                doc["code_content_data"] = code_payload["code"]
        except Exception:
            # Keep workflow robust for nodes that don't have code ranges.
            doc["code_content_data"] = ""
        return doc

    async def get_code_content(self, node_id: str) -> str:
        """Fetch only code content for a node without hydrating full doc."""
        try:
            code_payload = await self.code_service.get_code(node_id)
            if code_payload and code_payload.get("code"):
                return code_payload["code"]
        except Exception:
            return ""
        return ""
