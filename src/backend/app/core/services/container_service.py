

from app.core.model.edges import ContainsEdge

from app.core.repository import Repositories
from app.core.model.properties import ThemeConfig


class ContainerService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def get_by_qname(self, qname: str):
        return self.repos.class_repo.find_by_qname(qname)

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

    def update_theme_config(self, container_id: str, theme_config: ThemeConfig):
        return self.repos.nodes.update(container_id, theme_config)
