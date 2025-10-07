from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition


class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(
        self,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,
    ):
        class_node = ClassNode(
            name=name,
            qname=qname,
            description=description,
            implements=[qname],
            position=position,
        )
        return self.repos.class_repo.create(class_node)

    def get(self, class_id: str):
        return self.repos.class_repo.get_by_id(class_id)

    def update(self, class_node: ClassNode):
        return self.repos.class_repo.update(class_node.key, class_node)

    def delete(self, class_key: str):
        class_id = f"nodes/{class_key}"

        descendants = self.repos.class_repo.get_containment_tree(
            class_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            self.repos.nodes.delete(key)

        return self.repos.class_repo.delete(class_key)

    def add_function(self, parent_class_id: str, function_id: str):
        return self.add_child_to_container(
            parent_class_id,
            function_id,
            "class_to_function",
        )

    def add_call(self, parent_class_id: str, call_id: str):
        return self.add_child_to_container(
            parent_class_id,
            call_id,
            "class_to_call",
        )

    def add_class(self, parent_class_id: str, class_id: str):
        return self.add_child_to_container(
            parent_class_id,
            class_id,
            "class_to_class",
        )

    def get_children(self, class_id: str):
        return self.repos.class_repo.get_containment_tree(class_id)

    def get_code(self, class_id: str):
        class_node = self.repos.class_repo.get_by_id(class_id)
        if not class_node:
            return None

        file_doc, project_doc = self._resolve_file_and_project(class_node.id)
        if not file_doc or not project_doc:
            return None

        abs_path = self._build_abs_file_path(
            project_doc.get("path"),
            file_doc.get("path"),
        )
        code = self._extract_code_from_file(
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
