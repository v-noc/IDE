from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FunctionNode
from app.core.model.properties import CodePosition
from typing import Optional


class FunctionService(ContainerService):
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
        function = FunctionNode(
            name=name,
            qname=qname,
            description=description,
            position=position,
        )
        if _key:
            function.key = _key
        return await self.repos.function_repo.create(function)

    async def get(self, function_id: str):
        return await self.repos.function_repo.get_by_id(function_id)

    async def update(self, function: FunctionNode):
        return await self.repos.function_repo.update(function.key, function)

    async def delete(self, function_key: str):
        function_id = f"nodes/{function_key}"

        descendants = await self.repos.function_repo.get_containment_tree(
            function_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            await self.repos.nodes.delete(key)

        return await self.repos.function_repo.delete(function_key)

    async def add_function(self, parent_function_id: str, function_id: str):
        return await self.add_child_to_container(
            parent_function_id,
            function_id,
            "function_to_function",
        )

    async def add_call(self, parent_function_id: str, call_id: str):
        return await self.add_child_to_container(
            parent_function_id,
            call_id,
            "function_to_call",
        )

    async def add_class(self, parent_function_id: str, class_id: str):
        return await self.add_child_to_container(
            parent_function_id,
            class_id,
            "function_to_class",
        )

    async def get_children(self, function_id: str):
        return await self.repos.function_repo.get_containment_tree(function_id)

    async def get_code(self, function_id: str):
        function = await self.repos.function_repo.get_by_id(function_id)
        if not function:
            return None

        file_doc, project_doc = await self._resolve_file_and_project(function.id)
        if not file_doc or not project_doc:
            return None

        abs_path = await self._build_abs_file_path(
            project_doc.get("path"),
            file_doc.get("path"),
        )
        code = await self._extract_code_from_file(
            abs_path,
            function.position,
        )

        return {
            "id": function.id,
            "name": function.name,
            "node_type": function.node_type,
            "qname": function.qname,
            "file_path": file_doc.get("path"),
            "file_name": file_doc.get("name"),
            "position": function.position.model_dump(),
            "code": code,
        }
