

from app.core.model.edges import ContainsEdge

from app.core.repository import Repositories
from app.core.model.properties import ThemeConfig, CodePosition
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

    def add_child_to_container(
        self,
        container_id: str,
        child_id: str,
        contain_type: Optional[str] = None,

    ):
        container = self.repos.nodes.get_by_id(container_id)
        if not container:
            raise ValueError(f"Container {container_id} not found")

        child = self.repos.nodes.get_by_id(child_id)
        if not child:
            raise ValueError(f"Child {child_id} not found")

        if contain_type is None:
            contain_type = f"{container.node_type.lower()}_to_{child.node_type.lower()}"

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
            parents = self.repos.nodes.get_parent(current_id)
            if not parents:
                break
            parent_info = parents[0]
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
                while i < len(part) and i < start_col and part[i] in (" ", "\t"):
                    i += 1
                normalized.append(part[i:])
            collected = normalized

        return "\n".join(collected)
