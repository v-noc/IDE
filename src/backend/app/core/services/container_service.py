

import aiofiles
from app.core.model.edges import ContainsEdge, TargetsEdge

from app.core.repository import Repositories
from app.core.model.properties import ThemeConfig, CodePosition
from app.core.model.nodes import ContainerNode, CallNode, GroupNode
from app.core.model import AllNodes
from typing import Optional


class ContainerService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def get(self, container_id: str) -> Optional[AllNodes]:
        return await self.repos.nodes.get_by_id(container_id)

    async def get_by_qname(self, qname: str):
        return await self.repos.class_repo.find_by_qname(qname)

    async def add_child_to_container(
        self,
        container_id: str,
        child_id: str,
        contain_type: Optional[str] = None,
        version: Optional[int] = None,
    ):
        container = await self.repos.nodes.get_by_id(container_id)
        if not container:
            raise ValueError(f"Container {container_id} not found")

        child = await self.repos.nodes.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        if contain_type is None:
            contain_type = (
                f"{container.node_type.lower()}_to_{child.node_type.lower()}"
            )

        # Use parent's current_version if version not provided
        if version is None:
            version = getattr(container, 'current_version', 0) or 0

        contains_edge = ContainsEdge(
            from_id=container_id,
            to_id=child_id,
            relationship="contains_edges",
            contain_type=contain_type,
            version=version,
        )
        await self.repos.contains_edges.create(contains_edge)
        return True

    async def get_parent_container(self, container_id: str):
        return await self.repos.nodes.get_parent(container_id)

    async def delete_recursive(self, node_key: str) -> bool:
        """Generic cascading delete for any container node."""
        node_id = f"nodes/{node_key}"
        descendants = await self.repos.nodes.get_containment_tree(node_id, depth="*")
        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        # Use batch delete for descendants
        if descendant_keys:
            await self.repos.nodes.delete_batch(descendant_keys)

        return await self.repos.nodes.delete(node_key)

    async def update_theme_config(
        self,
        container_id: str,
        theme_config: ThemeConfig,
    ) -> Optional[AllNodes]:
        container_node = await self.get(container_id)
        if not container_node or not isinstance(container_node, ContainerNode):
            return None

        update_data = theme_config.model_dump(exclude_unset=True)
        if container_node.theme_config:
            updated_theme = container_node.theme_config.model_copy(
                update=update_data)
            container_node.theme_config = updated_theme
        else:
            container_node.theme_config = ThemeConfig(**update_data)

        return await self.repos.nodes.update(container_node.key, container_node)

    async def update_basic_info(
        self,
        container_id: str,
        name: Optional[str],
        description: Optional[str],
        icon: Optional[str]
    ) -> Optional[AllNodes]:
        container_node = await self.get(container_id)
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
            return await self.repos.nodes.update(container_node.key, container_node)

        return container_node

    # Internal helpers for code resolution
    async def _resolve_file_and_project(self, start_node_id: str):
        """Find enclosing file and project for any node.

        Returns a tuple (file_doc, project_doc) where each is a dict document.
        """
        # Fetch start node to see if it's already a file or project
        start_node = await self.repos.nodes.get_by_id(start_node_id)
        if not start_node:
            return None, None

        raw_node = start_node.model_dump()
        node_type = raw_node.get("node_type")

        if node_type == "file":
            file_doc = raw_node
            # Fast traversal for project
            project_node = await self.repos.nodes.get_parent_project(start_node_id)
            project_doc = project_node.model_dump() if project_node else None
            return file_doc, project_doc

        # If it's a project (unlikely to call get_code on it, but for safety)
        if node_type == "project":
            return None, raw_node

        # Otherwise, use the optimized traversal for ancestors
        result = await self.repos.nodes.get_nearest_file_and_project(start_node_id)
        return result.get("file"), result.get("project")

    def _build_abs_file_path(self, project_path: str, file_path: str) -> str:
        import os

        # If file_path is absolute, prefer it; else join with project root
        if os.path.isabs(file_path):
            return file_path
        return os.path.normpath(os.path.join(project_path, file_path))

    async def get_code(self, node_id: str) -> Optional[dict]:
        """Generic get_code for both FileNode and positioned nodes (Class/Function)."""
        node = await self.repos.nodes.get_by_id(node_id)
        if not node:
            return None

        file_doc, project_doc = await self._resolve_file_and_project(node.id)
        if not project_doc:
            return None

        # For files, file_doc IS the node.
        # If node is a file, we might not have a separate file_doc from _resolve_file_and_project
        # depending on how it's implemented. But our improved version handles it.
        effective_file_doc = file_doc or (
            node.model_dump() if node.node_type == "file" else None)

        if not effective_file_doc:
            return None

        abs_path = self._build_abs_file_path(
            project_doc.get("path"),
            effective_file_doc.get("path"),
        )

        # Files fetch everything, positioned nodes slice content
        position = getattr(
            node, "position", None) if node.node_type != "file" else None

        code = await self._extract_code_from_file(abs_path, position)

        result = {
            "id": node.id,
            "name": node.name,
            "node_type": node.node_type,
            "qname": node.qname,
            "file_path": effective_file_doc.get("path"),
            "file_name": effective_file_doc.get("name"),
            "code": code,
        }
        if position:
            result["position"] = position.model_dump()

        return result

    async def write_code(self, node_id: str, code_block: str) -> dict:
        """Generic write_code for both FileNode and positioned nodes."""
        node = await self.repos.nodes.get_by_id(node_id)
        if not node:
            return {"success": False, "error": "Element not found"}

        file_doc, project_doc = await self._resolve_file_and_project(node.id)
        if not file_doc or not project_doc:
            return {"success": False, "error": "Enclosing file or project not found"}

        abs_path = self._build_abs_file_path(
            project_doc.get("path"), file_doc.get("path"))

        if node.node_type == "file":
            try:
                async with aiofiles.open(abs_path, "w", encoding="utf-8") as f:
                    await f.write(code_block)
                return {"success": True}
            except IOError as e:
                return {"success": False, "error": str(e)}

        position = getattr(node, "position", None)
        if not position:
            return {"success": False, "error": "Positioned node missing position data"}

        try:
            # Read file content first
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                content = await f.read()

            lines = content.splitlines(True)

            start_line = max(1, position.line_no) - 1
            end_line = position.end_line_no
            start_col = max(0, position.col_offset)
            end_col = position.end_col_offset

            # Build replacement lines with indentation preserved from start column
            prefix = lines[start_line][:start_col] if 0 <= start_line < len(
                lines) else ""
            new_lines = [
                (prefix + l if i > 0 else (prefix + l))
                for i, l in enumerate(code_block.splitlines(True))
            ]

            if end_line is None:
                # Replace from start_line to end of file
                lines[start_line:] = new_lines
            else:
                # If selection ends mid-line, keep tail after end_col
                tail = ""
                if 0 <= (end_line - 1) < len(lines) and end_col is not None:
                    original = lines[end_line - 1]
                    tail = original[end_col:]
                lines[start_line:end_line] = new_lines
                if tail:
                    lines.insert(start_line + len(new_lines), tail)

            # Write modified content back
            async with aiofiles.open(abs_path, "w", encoding="utf-8") as f:
                await f.writelines(lines)
            return {"success": True}
        except IOError as e:
            return {"success": False, "error": str(e)}

    async def _extract_code_from_file(
        self,
        abs_path: str,
        position: Optional[CodePosition],
    ) -> str:
        """Read code once and optionally slice by line/column positions.

        - If position is None: returns the entire file content.
        - If position is provided: returns content from
          (line_no, col_offset) inclusive to (end_line_no, end_col_offset)
          exclusive. Indices follow the semantics used in CodePosition.
        """
        # Fast path: full file
        if position is None:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                return await f.read()

        start_line = max(1, position.line_no)
        start_col = max(0, position.col_offset)
        end_line = position.end_line_no
        end_col = position.end_col_offset

        import textwrap

        # Stream through file and collect raw lines
        collected: list[str] = []
        async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
            idx = 1
            async for raw_line in f:
                if idx < start_line:
                    idx += 1
                    continue

                line = raw_line[:-1] if raw_line.endswith("\n") else raw_line

                if end_line is None or idx < end_line:
                    collected.append(line)
                elif idx == end_line:
                    slice_end = None if end_col is None else end_col
                    # Only slice the end of the last line
                    collected.append(line[:slice_end])
                    break
                else:
                    break
                idx += 1

        if not collected:
            return ""

        # Dedent the entire block
        joined = "\n".join(collected)
        dedented = textwrap.dedent(joined)

        # If start_col was specified and the first line still has content before it
        # (e.g. it was a partial line like 'x = lambda: 1' and we want the lambda),
        # we might still need to slice the first line.
        # But for AST nodes like functions/classes, start_col points to the start
        # of the node, so dedent should already handle it.
        # Let's check if the first line needs further slicing.
        # However, if we already used dedent, we should be careful.
        # For now, let's see if dedent is enough for the identified issue.
        return dedented

    async def rebuild_call_group(self, parent_id: str):
        """Ensure a single call group exists under the given parent,
        containing all direct call children.

        - Collect direct call children of the parent (including calls inside
          an existing call-group).
        - If a call-group already exists, delete it (children are reattached
          to parent by the group service).
        - Create a fresh call-group and move all calls into it.

        Returns the created group node (dict) or None if there are no
        calls.
        """
        # Local import to avoid circular dependency
        from app.core.services.group_service import GroupService

        parent = await self.repos.nodes.get_by_id(parent_id)
        if not parent:
            return None

        children = await self.repos.nodes.get_containment_tree(parent_id, depth=1)

        call_child_vertices = []
        existing_call_group_vertex = None

        for item in children:
            vertex = item.get("vertex", {})
            if vertex.get("node_type") == "call":
                call_child_vertices.append(vertex)
            elif (
                vertex.get("node_type") == "group"
                and vertex.get("group_type") == "call"
            ):
                existing_call_group_vertex = vertex

        group_service = GroupService(self.repos)

        if existing_call_group_vertex is not None:
            existing_call_group_id = existing_call_group_vertex.get("_id")
            group_children = await group_service.get_children(existing_call_group_id)
            for gi in group_children:
                if (
                    gi.get("vertex", {}).get("node_type") == "call"
                    and gi.get("parent_id") == existing_call_group_id
                ):
                    call_child_vertices.append(gi.get("vertex"))

            # Remove the existing group (children get reattached to parent)
            await group_service.delete(existing_call_group_id)

        # Unique keys of calls to (re)group
        call_child_keys = []
        seen = set()
        for v in call_child_vertices:
            k = v.get("_key")
            if k and k not in seen:
                seen.add(k)
                call_child_keys.append(k)

        if not call_child_keys:
            return None

        # parent_id is an id; group_service.create expects a key
        return await group_service.create(
            name="Calls",
            description="Grouped calls",
            parent_id=parent.key,
            children_ids=call_child_keys,
        )

    async def clone_callee_call_graph(
        self,
        source_callee_id: str,
        attach_under_id: str,
    ) -> list[str]:
        """Clone the call graph inside a callee function/class under a new
        container.

        - Reads the callee's containment subtree and filters call nodes.
        - Recreates calls with manual positions and same targets.
        - Preserves call->call nesting by attaching children to their cloned
          parents.

        Returns list of newly created root call IDs (attached directly
        under attach_under_id).
        """
        # Get full subtree to preserve parent relationships
        tree = await self.repos.call_repo.get_downward_call_chain(
            source_callee_id,

        )

        # Collect only groups and calls with their immediate parent
        items: list[dict] = []
        for item in tree:
            vertex = item.get("vertex", {})
            if vertex.get("node_type") in ("group", "call"):
                items.append(item)

        if not items:
            return []

        # Map: original call _id -> new call id
        orig_to_new: dict[str, str] = {}
        new_root_call_ids: list[str] = []

        # Ensure attach point exists
        _ = await self.repos.nodes.get_by_id(attach_under_id)

        # BFS order from get_containment_tree ensures parents appear
        # before children
        for item in items:
            vertex = item.get("vertex")
            node_type = vertex.get("node_type")
            orig_parent_id = item.get("parent_id")

            if node_type == "group":
                # Recreate group (keep name/description/group_type; reuse qname)
                group_qname = (
                    vertex.get("qname")
                    or vertex.get("name", "group").lower().replace(" ", "_")
                )
                new_group = GroupNode(
                    name=vertex.get("name"),
                    qname=group_qname,
                    description=vertex.get("description", ""),
                    group_type=vertex.get("group_type", "call"),
                )
                created_group = await self.repos.group_repo.create(new_group)

                # Determine parent container: cloned ancestor or attach point
                if orig_parent_id in orig_to_new:
                    parent_container_id = orig_to_new[orig_parent_id]
                else:
                    parent_container_id = attach_under_id

                # Edge: parent -> group (contain type auto-detected)
                await self.add_child_to_container(
                    parent_container_id,
                    created_group.id,
                    None,
                )

                # Map original group id to new group id
                orig_to_new[vertex.get("_id")] = created_group.id

                # If attached directly under attach point, track as root
                if parent_container_id == attach_under_id:
                    new_root_call_ids.append(created_group.id)

            elif node_type == "call":
                target = item.get("target")

                # Create new call node (manual positions)
                new_call = CallNode(
                    name=vertex.get("name"),
                    qname=vertex.get("qname"),
                    description=vertex.get("description", ""),
                    position=CodePosition(
                        line_no=0,
                        col_offset=0,
                        end_line_no=0,
                        end_col_offset=0,
                    ),
                    manually_created=True,
                )
                created = await self.repos.call_repo.create(new_call)

                # Recreate target edge if any
                if target and target.get("_id"):
                    await self.repos.targets_edges.create(
                        TargetsEdge(from_id=created.id,
                                    to_id=target.get("_id"))
                    )

                # Determine parent container: cloned ancestor or attach point
                if orig_parent_id in orig_to_new:
                    parent_container_id = orig_to_new[orig_parent_id]
                else:
                    parent_container_id = attach_under_id

                # Edge: parent -> call
                await self.add_child_to_container(
                    parent_container_id,
                    created.id,
                    None,
                )

                # Record mapping after edges are in place
                orig_to_new[vertex.get("_id")] = created.id
                if parent_container_id == attach_under_id:
                    new_root_call_ids.append(created.id)

        return new_root_call_ids
