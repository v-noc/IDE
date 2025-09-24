from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition


class ClassService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, name: str, qname: str, description: str, path: str, position: CodePosition):
        class_node = ClassNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
            position=position,
        )
        return self.repos.class_repo.create(class_node)

    def get(self, class_id: str):
        return self.repos.class_repo.get_by_id(class_id)

    def update(self, class_node: ClassNode):
        return self.repos.class_repo.update(class_node.key, class_node)

    def delete(self, class_key: str):
        return self.repos.class_repo.delete(class_key)

    def add_function_to_class(self, parent_class_id: str, function_id: str):
        return self.add_child_to_container(parent_class_id, function_id, "class_to_function")

    def add_call_to_class(self, parent_class_id: str, call_id: str):
        return self.add_child_to_container(parent_class_id, call_id, "class_to_call")

    def add_class_to_class(self, parent_class_id: str, class_id: str):
        return self.add_child_to_container(parent_class_id, class_id, "class_to_class")

    def get_children(self, class_id: str):
        return self.repos.class_repo.get_containment_tree(class_id)
