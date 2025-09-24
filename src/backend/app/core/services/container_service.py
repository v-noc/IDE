

from app.core.model.edges import ContainsEdge

from app.core.repository import Repositories


class ContainerService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def add_child_to_container(self, container_id: str, child_id: str, contain_type: str):
        container = self.repos.nodes.get_by_id(container_id)
        if not container:
            raise ValueError(f"Container {container_id} not found")

        child = self.repos.nodes.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        contains_edge = ContainsEdge(
            from_id=container_id,
            to_id=child_id,
            relationship="contains_edges",
            contain_type=contain_type
        )
        self.repos.contains_edges.create(contains_edge)
        return True

    def get_parent_container(self, container_id: str):
        return self.repos.nodes.get_parent(container_id)
