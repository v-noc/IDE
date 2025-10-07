from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FileNode


class FileService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str, path: str, hash: str):
        file = FileNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
            hash=hash,
        )
        return self.repos.file_repo.create(file)

    def get(self, file_id: str):
        return self.repos.file_repo.get_by_id(file_id)

    def update(self, file: FileNode):
        return self.repos.file_repo.update(file.key, file)

    def delete(self, file_key: str):
        return self.repos.file_repo.delete(file_key)

    def add_function(self, file_id: str, function_id: str):
        return self.add_child_to_container(
            file_id,
            function_id,
            "file_to_function",
        )

    def add_call(self, file_id: str, call_id: str):
        return self.add_child_to_container(
            file_id,
            call_id,
            "file_to_call",
        )

    def add_class(self, file_id: str, class_id: str):
        return self.add_child_to_container(
            file_id,
            class_id,
            "file_to_class",
        )

    def get_children(self, file_id: str):
        return self.repos.file_repo.get_containment_tree(file_id)

    def get_code(self, file_id: str):
        file = self.repos.file_repo.get_by_id(file_id)
        if not file:
            return None

        # Resolve project root by walking parents
        file_doc, project_doc = self._resolve_file_and_project(
            file.id,
        )
        # When called on the file itself, file_doc may be None; use current
        # file
        effective_file = file_doc or file.model_dump()
        if not project_doc:
            return None

        project_path = project_doc.get("path")
        file_path = effective_file.get("path")
        abs_path = self._build_abs_file_path(
            project_path,
            file_path,
        )

        content = self._extract_code_from_file(
            abs_path,
            None,
        )

        result = {
            "file_id": file.id,
            "file_name": file.name,
            "file_path": file.path,
            "node_type": file.node_type,
            "qname": file.qname,
            "code": content,
        }
        return result
