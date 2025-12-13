

from app.core.model.edges import ContainsEdge, TargetsEdge

from app.core.repository import Repositories
from app.core.model.properties import ThemeConfig, CodePosition
from app.core.model.nodes import ContainerNode, CallNode, GroupNode
from app.core.model import AllNodes
from typing import Optional


class ContainerService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def get(self, container_id: str) -> Optional[AllNodes]:
        return self.repos.nodes.get_by_id(container_id)

    def get_by_qname(self, qname: str):
        return self.repos.class_repo.find_by_qname(qname)

    def add_child_to_container(
        self,
        container_id: str,
        child_id: str,
        contain_type: Optional[str] = None,
        version: Optional[int] = None,
    ):
        container = self.repos.nodes.get_by_id(container_id)
        if not container:
            raise ValueError(f"Container {container_id} not found")

        child = self.repos.nodes.get_by_id(child_id)
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
        self.repos.contains_edges.create(contains_edge)
        return True

    def get_parent_container(self, container_id: str):
        return self.repos.nodes.get_parent(container_id)

    def update_theme_config(
        self,
        container_id: str,
        theme_config: ThemeConfig,
    ) -> Optional[AllNodes]:
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

    # Internal helpers for code resolution
    def _resolve_file_and_project(self, start_node_id: str):
        """Walk parents via contains edges to find enclosing file and project.

        Returns a tuple (file_doc, project_doc) where each is a dict document.
        Any missing ancestor returns (None, None) accordingly.
        """
        current_id = start_node_id
        file_doc = None
        project_doc = None

        # Limit the ascent to avoid infinite loops
        for _ in range(50):
            parent_info = self.repos.nodes.get_parent(current_id)

            if not parent_info:
                break

            parent_vertex = parent_info.get("vertex") or {}
            parent_id = parent_vertex.get("_id")
            node_type = parent_vertex.get("node_type")

            if node_type == "file" and file_doc is None:
                file_doc = parent_vertex
            if node_type == "project":
                project_doc = parent_vertex
                # We can stop once we reach project
                break

            if not parent_id:
                break
            current_id = parent_id

        if project_doc is None:
            project_doc = self.repos.nodes.get_parent_project(
                file_doc.get("_id"))

            if project_doc is None:
                return None, None
        return file_doc, project_doc

    def _build_abs_file_path(self, project_path: str, file_path: str) -> str:
        import os

        # If file_path is absolute, prefer it; else join with project root
        if os.path.isabs(file_path):
            return file_path
        return os.path.normpath(os.path.join(project_path, file_path))

    def _extract_code_from_file(
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
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()

        start_line = max(1, position.line_no)
        start_col = max(0, position.col_offset)
        end_line = position.end_line_no
        end_col = position.end_col_offset

        # Stream through file only once
        collected: list[str] = []
        with open(abs_path, "r", encoding="utf-8") as f:
            for idx, raw_line in enumerate(f, start=1):
                if idx < start_line:
                    continue

                # Normalize by removing trailing newline; we rejoin with \n
                line = raw_line[:-1] if raw_line.endswith("\n") else raw_line

                if end_line is None or idx < end_line:
                    if idx == start_line:
                        collected.append(line[start_col:])
                    else:
                        collected.append(line)
                elif idx == end_line:
                    slice_end = None if end_col is None else end_col
                    if idx == start_line:
                        collected.append(line[start_col:slice_end])
                    else:
                        collected.append(line[:slice_end])
                    break
                else:
                    break

        # Normalize indentation across lines when selection starts mid-line
        if start_col > 0 and len(collected) > 1:
            normalized: list[str] = []
            normalized.append(collected[0])
            for part in collected[1:]:
                # Count leading spaces/tabs and trim up to start_col
                i = 0
                while (
                    i < len(part)
                    and i < start_col
                    and part[i] in (" ", "\t")
                ):
                    i += 1
                normalized.append(part[i:])
            collected = normalized

        return "\n".join(collected)

    def rebuild_call_group(self, parent_id: str):
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

        parent = self.repos.nodes.get_by_id(parent_id)
        if not parent:
            return None

        children = self.repos.nodes.get_containment_tree(parent_id, depth=1)

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
            group_children = group_service.get_children(existing_call_group_id)
            for gi in group_children:
                if (
                    gi.get("vertex", {}).get("node_type") == "call"
                    and gi.get("parent_id") == existing_call_group_id
                ):
                    call_child_vertices.append(gi.get("vertex"))

            # Remove the existing group (children get reattached to parent)
            group_service.delete(existing_call_group_id)

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
        return group_service.create(
            name="Calls",
            description="Grouped calls",
            parent_id=parent.key,
            children_ids=call_child_keys,
        )

    def clone_callee_call_graph(
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
        tree = self.repos.call_repo.get_downward_call_chain(
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
        _ = self.repos.nodes.get_by_id(attach_under_id)

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
                created_group = self.repos.group_repo.create(new_group)

                # Determine parent container: cloned ancestor or attach point
                if orig_parent_id in orig_to_new:
                    parent_container_id = orig_to_new[orig_parent_id]
                else:
                    parent_container_id = attach_under_id

                # Edge: parent -> group (contain type auto-detected)
                self.add_child_to_container(
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
                created = self.repos.call_repo.create(new_call)

                # Recreate target edge if any
                if target and target.get("_id"):
                    self.repos.targets_edges.create(
                        TargetsEdge(from_id=created.id,
                                    to_id=target.get("_id"))
                    )

                # Determine parent container: cloned ancestor or attach point
                if orig_parent_id in orig_to_new:
                    parent_container_id = orig_to_new[orig_parent_id]
                else:
                    parent_container_id = attach_under_id

                # Edge: parent -> call
                self.add_child_to_container(
                    parent_container_id,
                    created.id,
                    None,
                )

                # Record mapping after edges are in place
                orig_to_new[vertex.get("_id")] = created.id
                if parent_container_id == attach_under_id:
                    new_root_call_ids.append(created.id)

        return new_root_call_ids
