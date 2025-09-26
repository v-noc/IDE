from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import CallNode
from app.core.model.properties import CodePosition
from app.core.model.edges import TargetsEdge


class CallService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str,  position: CodePosition, target_id: str):
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
        return self.repos.call_repo.delete(call_key)

    def add_call(self, parent_call_id: str, call_id: str):
        return self.add_child_to_container(parent_call_id, call_id, "call_to_call")

    def get_children(self, call_id: str):
        return self.repos.call_repo.get_containment_tree(call_id)
