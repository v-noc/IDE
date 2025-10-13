from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import CallNode
from app.core.model.properties import CodePosition
from app.core.model.edges import TargetsEdge


class CallService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(
        self,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,
        target_id: str,
    ):
        call = CallNode(
            name=name,
            qname=qname,
            description=description,
            position=position,

        )

        new_call = self.repos.call_repo.create(call)
        target = TargetsEdge(
            from_id=new_call.id,
            to_id=target_id,
        )
        self.repos.targets_edges.create(target)
        return new_call

    def get(self, call_id: str):
        return self.repos.call_repo.get_by_id(call_id)

    def update(self, call: CallNode):
        return self.repos.call_repo.update(call.key, call)

    def delete(self, call_key: str):
        call_id = f"nodes/{call_key}"

        descendants = self.repos.call_repo.get_containment_tree(
            call_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            self.repos.nodes.delete(key)

        return self.repos.call_repo.delete(call_key)

    def add_call(self, parent_call_id: str, call_id: str):
        return self.add_child_to_container(
            parent_call_id,
            call_id,
            "call_to_call",
        )

    def get_children(self, call_id: str):
        return self.repos.call_repo.get_containment_tree(call_id)

    def get_code(self, call_id: str):
        call = self.repos.call_repo.get_by_id(call_id)
        if not call:
            return None

        file_doc, project_doc = self._resolve_file_and_project(call.id)
        if not file_doc or not project_doc:
            return None

        abs_path = self._build_abs_file_path(
            project_doc.get("path"),
            file_doc.get("path"),
        )
        code = self._extract_code_from_file(
            abs_path,
            call.position,
        )

        return {
            "id": call.id,
            "name": call.name,
            "node_type": call.node_type,
            "qname": call.qname,
            "file_path": file_doc.get("path"),
            "file_name": file_doc.get("name"),
            "position": call.position.model_dump(),
            "code": code,
        }

    def get_call_with_parent_and_target(self, parent_id: str, target_id: str):
        # Note: repository expects (target_id, parent_id)
        return self.repos.call_repo.find_call_by_target_parent(
            target_id,
            parent_id,
        )

    def get_call_parent_chain(self, call_id: str):
        return self.repos.call_repo.find_upward_call_chain(call_id)
