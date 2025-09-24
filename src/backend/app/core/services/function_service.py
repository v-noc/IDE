from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FunctionNode
from app.core.model.properties import CodePosition


class FunctionService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str,  position: CodePosition):
        function = FunctionNode(
            name=name,
            qname=qname,
            description=description,

            position=position,
        )
        return self.repos.function_repo.create(function)

    def get(self, function_id: str):
        return self.repos.function_repo.get_by_id(function_id)

    def update(self, function: FunctionNode):
        return self.repos.function_repo.update(function.key, function)

    def delete(self, function_key: str):
        return self.repos.function_repo.delete(function_key)

    def add_function_to_function(self, parent_function_id: str, function_id: str):
        return self.add_child_to_container(parent_function_id, function_id, "function_to_function")

    def add_call_to_function(self, parent_function_id: str, call_id: str):
        return self.add_child_to_container(parent_function_id, call_id, "function_to_call")

    def add_class_to_function(self, parent_function_id: str, class_id: str):
        return self.add_child_to_container(parent_function_id, class_id, "function_to_class")

    def get_children(self, function_id: str):
        return self.repos.function_repo.get_containment_tree(function_id)
