from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import GroupNode
from typing import Optional
from typing import List


class GroupService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    def remove_child_from_group(self, group_id: str, child_id: str):
        child = self.repos.nodes.get_by_key(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        group = self.repos.nodes.get_by_key(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        parent = self.repos.nodes.get_parent(group_id)
        if not parent:
            raise ValueError(f"Parent {child_id} not found")

        self._remove_child_from_group(group.id, child.id)

        self.add_child_to_container(
            parent.get("vertex").get("_id"),
            child.id,
            f"{parent.get('vertex').get('node_type').lower()}_to_{child.node_type}",
        )
        return True

    def _remove_child_from_group(self, group_id: str, child_id: str):
        group = self.repos.nodes.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        child = self.repos.nodes.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        contains_edge = self.repos.contains_edges.find_one(
            {
                "from_id": group_id,
                "to_id": child_id,
            }
        )
        if not contains_edge:
            raise ValueError(
                f"Contains edge for container {group_id} -{child_id} not found"
            )
        self.repos.contains_edges.delete(contains_edge.id)
        return True

    def add_child_to_group(self, group_id: str, child_id: str):

        child = self.repos.nodes.get_by_key(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        group = self.repos.nodes.get_by_key(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        parent = self.repos.nodes.get_parent(child.id)
        if not parent:
            raise ValueError(f"Parent {child_id} not found")

        self._remove_child_from_group(
            parent.get("vertex").get("_id"), child.id)
        return self.add_child_to_container(group.id, child.id)

    def delete(self, group_id: str, remove_children: bool = False):
        group = self.repos.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        children = self.repos.group_repo.get_containment_tree(group_id)
        if remove_children:
            for child in children:
                self._remove_child_from_group(
                    group_id, child.get("vertex").get("_id"))
                parent = self.repos.nodes.get_parent(group_id)
                if parent:
                    self.add_child_to_container(
                        parent.get("vertex").get("_id"),
                        group_id,
                        f"{parent.get('vertex').get('node_type').lower()}_to_{child.get('vertex').get('node_type')}",
                    )

        return self.repos.group_repo.delete(group.key)

    def create(
        self,
        name: str,
        description: str,
        parent_id: str,
        children_ids: List[str],
        qname: Optional[str] = None,
    ):
        parent = self.repos.nodes.get_by_key(parent_id)
        if not parent:
            raise ValueError(f"Parent {parent_id} not found")

        children = []
        for child_id in children_ids:
            child = self.repos.nodes.get_by_key(child_id)
            if not child:
                print(f"Child {child_id} not found")

                continue
            children.append(child)

        if qname is None:
            qname = name.lower().replace(" ", "_")

        group = GroupNode(
            name=name,
            qname=qname,
            description=description,
        )
        created_group = self.repos.group_repo.create(group)

        for child in children:
            # Removes the child from the previous parent
            self._remove_child_from_group(parent.id, child.id)
            # Adds the child to the new group
            self.add_child_to_container(
                created_group.id, child.id, f"group_to_{child.node_type.lower()}"
            )

        self.add_child_to_container(
            parent.id, created_group.id, f"{parent.node_type.lower()}_to_group"
        )

        return created_group

    def get_children(self, group_id: str):
        return self.repos.group_repo.get_containment_tree(group_id)
