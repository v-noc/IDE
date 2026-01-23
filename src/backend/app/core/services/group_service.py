from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import GroupNode
from typing import Optional
from typing import List


class GroupService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def remove_child_from_group(self, group_id: str, child_id: str):
        child = await self.repos.nodes.get_by_key(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        group = await self.repos.nodes.get_by_key(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        parent = await self.repos.nodes.get_parent(group.id)
        if not parent:
            raise ValueError(f"Parent {child_id} not found")

        await self._remove_child_from_group(group.id, child.id)

        await self.add_child(
            parent.get("vertex").get("_id"),
            child.id,
            f"{parent.get('vertex').get('node_type').lower()}_to_{child.node_type}",
        )
        return True

    async def _remove_child_from_group(self, group_id: str, child_id: str):
        group = await self.repos.nodes.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        child = await self.repos.nodes.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        contains_edge = await self.repos.contains_edges.find_one(
            {
                "from_id": group_id,
                "to_id": child_id,
            }
        )
        if not contains_edge:
            raise ValueError(
                f"Contains edge for container {group_id} -{child_id} not found"
            )
        await self.repos.contains_edges.delete(contains_edge.id)
        return True

    async def add_child_to_group(self, group_id: str, child_id: str):
        child = await self.repos.nodes.get_by_key(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        group = await self.repos.nodes.get_by_key(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        parent = await self.repos.nodes.get_parent(child.id)
        if not parent:
            raise ValueError(f"Parent {child_id} not found")

        await self._remove_child_from_group(
            parent.get("vertex").get("_id"), child.id)
        return await self.add_child(group.id, child.id)

    async def delete(self, group_id: str, remove_children: bool = False):
        group = await self.repos.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        children = await self.repos.group_repo.get_containment_tree(
            group.id, depth=1)

        for child in children:
            child_id = child.get("vertex").get("_id")
            child_key = child.get("vertex").get("_key")
            
            await self._remove_child_from_group(group.id, child_id)
            
            if remove_children:
                await self.repos.nodes.delete(child_key)
            else:
                parent = await self.repos.nodes.get_parent(group.id)
                if parent:
                    await self.add_child(
                        parent.get("vertex").get("_id"),
                        child_id,
                        f"{parent.get('vertex').get('node_type').lower()}_to_{child.get('vertex').get('node_type')}",
                    )

        return await self.repos.group_repo.delete(group.key)

    async def create(
        self,
        name: str,
        description: str,
        parent_id: str,
        children_ids: List[str],
        qname: Optional[str] = None,
    ):
        parent = await self.repos.nodes.get_by_key(parent_id)
        if not parent:
            raise ValueError(f"Parent {parent_id} not found")

        children = []
        group_type = "empty"

        # ToDO Add More checks for the group type
        for child_id in children_ids:
            child = await self.repos.nodes.get_by_key(child_id)

            if not child:
                print(f"Child {child_id} not found")

                continue

            if child.node_type == "function" or child.node_type == "class":
                group_type = "code"
            elif child.node_type == "folder" or child.node_type == "file":
                group_type = "folder_file"
            elif child.node_type == "call":
                group_type = "call"
            else:
                group_type = "empty"

            children.append(child)

        if qname is None:
            qname = name.lower().replace(" ", "_")

        group = GroupNode(
            name=name,
            qname=qname,
            description=description,
            group_type=group_type,
        )
        created_group = await self.repos.group_repo.create(group)

        for child in children:
            # Removes the child from the previous parent
            await self._remove_child_from_group(parent.id, child.id)
            # Adds the child to the new group
            await self.add_child(
                created_group.id, child.id, f"group_to_{child.node_type.lower()}"
            )

        await self.add_child(
            parent.id, created_group.id, f"{parent.node_type.lower()}_to_group"
        )

        return created_group

    async def get_children(self, group_id: str):
        return await self.repos.group_repo.get_containment_tree(group_id)
