

from app.core.model.edges import ContainsEdge

from app.core.repository import Repositories
from app.core.model.properties import ThemeConfig
from app.core.model.nodes import ContainerNode
from app.core.model import AllNodes
from typing import Optional


class ContainerService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def get(self, container_id: str) -> Optional[AllNodes]:
        return self.repos.nodes.get_by_id(container_id)

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

    def update_theme_config(self, container_id: str, theme_config: ThemeConfig) -> Optional[AllNodes]:
        container_node = self.get(container_id)
        if not container_node or not isinstance(container_node, ContainerNode):
            return None

        update_data = theme_config.model_dump(exclude_unset=True)
        if container_node.theme_config:
            updated_theme = container_node.theme_config.model_copy(
                update=update_data)
            container_node.theme_config = updated_theme
        else:
            container_node.theme_config = ThemeConfig(**update_data)

        return self.repos.nodes.update(container_node.key, container_node)

    def update_basic_info(
        self,
        container_id: str,
        name: Optional[str],
        description: Optional[str],
        icon: Optional[str]
    ) -> Optional[AllNodes]:
        container_node = self.get(container_id)
        if not container_node or not isinstance(container_node, ContainerNode):
            return None

        updated = False
        if name is not None:
            container_node.name = name
            updated = True
        if description is not None:
            container_node.description = description
            updated = True
        if icon is not None:
            container_node.icon = icon
            updated = True

        if updated:
            return self.repos.nodes.update(container_node.key, container_node)

        return container_node
