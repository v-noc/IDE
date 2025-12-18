from typing import Optional
from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition


class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def create(
        self,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,
        _key: Optional[str] = None,
    ):
        class_node = ClassNode(
            name=name,
            qname=qname,
            description=description,
            implements=[qname],
            position=position,
        )
        if _key:
            class_node.key = _key
        return await self.repos.class_repo.create(class_node)

    async def get(self, class_id: str):
        return await self.repos.class_repo.get_by_id(class_id)

    async def update(self, class_node: ClassNode):
        return await self.repos.class_repo.update(class_node.key, class_node)

    async def delete(self, class_key: str):
        class_id = f"nodes/{class_key}"

        descendants = await self.repos.class_repo.get_containment_tree(
            class_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            await self.repos.nodes.delete(key)

        return await self.repos.class_repo.delete(class_key)

    async def add_function(self, parent_class_id: str, function_id: str):
        return await self.add_child_to_container(
            parent_class_id,
            function_id,
            "class_to_function",
        )

    async def add_call(self, parent_class_id: str, call_id: str):
        return await self.add_child_to_container(
            parent_class_id,
            call_id,
            "class_to_call",
        )

    async def add_class(self, parent_class_id: str, class_id: str):
        return await self.add_child_to_container(
            parent_class_id,
            class_id,
            "class_to_class",
        )

    async def get_children(self, class_id: str):
        return await self.repos.class_repo.get_containment_tree(class_id)

    async def get_code(self, class_id: str):
        class_node = await self.repos.class_repo.get_by_id(class_id)
        if not class_node:
            return None

        file_doc, project_doc = await self._resolve_file_and_project(class_node.id)
        if not file_doc or not project_doc:
            return None

        abs_path = await self._build_abs_file_path(
            project_doc.get("path"),
            file_doc.get("path"),
        )
        code = await self._extract_code_from_file(
            abs_path,
            class_node.position,
        )

        return {
            "id": class_node.id,
            "name": class_node.name,
            "node_type": class_node.node_type,
            "qname": class_node.qname,
            "file_path": file_doc.get("path"),
            "file_name": file_doc.get("name"),
            "position": class_node.position.model_dump(),
            "code": code,
        }
