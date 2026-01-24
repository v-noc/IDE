from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import GroupNode
from typing import List, Optional, Set
from app.core.model.nodes import GroupNode


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

        # Validate type compatibility
        if not self._validate_group_type(group.group_type, child.node_type):
            raise ValueError(
                f"Cannot add {child.node_type} to {group.group_type} group"
            )
            
        return await self.add_child(group.id, child.id)

    async def delete(self, group_id: str, remove_children: bool = False):
        group = await self.repos.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Get the group's parent to re-attach children if preserving them
        parent = await self.repos.nodes.get_parent(group.id)
        if not remove_children and not parent:
             # If we want to preserve children, we MUST have a parent to move them to.
             # However, if the group is orphaned (no parent), we can't move them "up".
             # In that edge case, we should probably fail or force delete.
             # For now, let's raise error.
            raise ValueError("Cannot preserve children: group has no parent to move them to")

        parent_vertex = parent.get("vertex") if parent else None
        parent_id = parent_vertex.get("_id") if parent_vertex else None
        parent_type = parent_vertex.get("node_type") if parent_vertex else None

        children = await self.repos.nodes.get_containment_tree(
            group.id, depth=1)

        for child in children:
            child_vertex = child.get("vertex")
            child_id = child_vertex.get("_id")
            child_key = child_vertex.get("_key")
            child_type = child_vertex.get("node_type")
            
            # Use internal method to remove the edge
            await self._remove_child_from_group(group.id, child_id)
            
            if remove_children:
                await self.repos.nodes.delete(child_key)
            else:
                # Move child to group's parent
                if parent_id:
                     # Construct new edge type
                    contain_type = f"{parent_type.lower()}_to_{child_type}"
                    await self.add_child(
                        parent_id, 
                        child_id, 
                        contain_type
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

    def _validate_group_type(
        self,
        existing_type: str,
        new_child_type: str
    ) -> bool:
        """Check if adding this child type is valid for the group."""
        type_rules = {
            "call": {"call"},
            "code": {"function", "class", "group"},
            "folder_file": {"folder", "file", "group"},
            "empty": set(),  # "empty" needs special handling or just allow first item to set type
        }
        
        # If group is strictly empty, we might allow the first child to define it.
        # But here we just check compatibility against predefined rules.
        if existing_type == "empty":
             # If it's empty, we allow anything that CAN be grouped.
             # But technically, we should check against what valid groups ARE.
             # For now, let's assume empty accepts common types.
             return new_child_type in {"folder", "file", "function", "class", "call", "group"}
             
        allowed = type_rules.get(existing_type, set())
        return new_child_type in allowed

    def _infer_group_type(self, child_types: List[str]) -> str:
        """Infer the appropriate group type from child node types."""
        type_set = set(child_types)
        
        if not type_set:
            return "empty"
        
        if type_set == {"call"}:
            return "call"
        
        if type_set.issubset({"function", "class", "group"}):
            return "code"
        
        if type_set.issubset({"folder", "file", "group"}):
            return "folder_file"
        
        # Fallback for mixed or invalid
        return "empty"
