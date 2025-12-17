from app.core.services.container_service import ContainerService
from app.core.repository import Repositories
from app.core.model.nodes import FileNode
from typing import Optional


class FileService(ContainerService):
    def __init__(self, repos: Repositories):
        self.repos = repos

    async def create(self, name: str, qname: str, description: str, path: str, hash: str):
        file = FileNode(
            name=name,
            qname=qname,
            description=description,
            path=path,
            hash=hash,
        )
        return await self.repos.file_repo.create(file)

    async def write_code_by_id(self, node_key: str, code_block: str):
        """Writes code for an element identified by its document key.

        - For a file node: overwrite full file content with code_block
        - For function/class/call nodes: replace the slice defined by position
        """
        # Fetch raw to determine type and full id
        raw_node = await self.repos.nodes.get_raw_by_key(node_key)
        if not raw_node:
            return {"success": False, "error": "Element not found"}

        node_type = raw_node.get("node_type")
        full_id = raw_node.get("_id")  # e.g., nodes/123
        if not node_type or not full_id:
            return {"success": False, "error": "Corrupted element data"}

        # Resolve enclosing file and project for absolute path
        if node_type == "file":
            file_doc = await self.repos.file_repo.get_by_id(full_id)
            project_doc = await self.repos.nodes.get_parent_project(full_id)

            abs_path = await self._build_abs_file_path(
                project_doc.get("path"), file_doc.path)

            # Fallback: overwrite full file if no position
            try:
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(code_block)
                return {"success": True}
            except IOError as e:
                return {"success": False, "error": str(e)}
        else:
            file_doc, project_doc = await self._resolve_file_and_project(full_id)
            if not file_doc or not project_doc:
                return {"success": False, "error": "Enclosing file or project not found"}

            abs_path = self._build_abs_file_path(
                project_doc.get("path"), file_doc.get("path"))

            typed_node = await self.repos.nodes.get_by_id(full_id)
            position: Optional[object] = getattr(typed_node, "position", None)

            # Replace code slice defined by CodePosition
            try:
                with open(abs_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()

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

                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()
                return {"success": True}
            except IOError as e:
                return {"success": False, "error": str(e)}

    async def get(self, file_id: str):
        return await self.repos.file_repo.get_by_id(file_id)

    async def update(self, file: FileNode):
        return await self.repos.file_repo.update(file.key, file)

    async def delete(self, file_key: str):
        file_id = f"nodes/{file_key}"

        descendants = await self.repos.file_repo.get_containment_tree(
            file_id, depth="*")

        descendant_keys = [item["vertex"]["_key"] for item in descendants]

        for key in reversed(descendant_keys):
            await self.repos.nodes.delete(key)

        return await self.repos.file_repo.delete(file_key)

    async def add_function(self, file_id: str, function_id: str):
        return await self.add_child_to_container(
            file_id,
            function_id,
            "file_to_function",
        )

    async def add_call(self, file_id: str, call_id: str):
        return await self.add_child_to_container(
            file_id,
            call_id,
            "file_to_call",
        )

    async def add_class(self, file_id: str, class_id: str):
        return await self.add_child_to_container(
            file_id,
            class_id,
            "file_to_class",
        )

    async def get_children(self, file_id: str):
        return await self.repos.file_repo.get_containment_tree(file_id)

    async def get_code(self, file_id: str):
        file = await self.repos.file_repo.get_by_id(file_id)

        if not file:
            return None

        # Resolve project root by walking parents
        project_doc = await self.repos.nodes.get_parent_project(
            file.id,
        )

        file_doc = await self.repos.file_repo.get_by_id(file.id)

        # When called on the file itself, file_doc may be None; use current
        # file
        effective_file = file_doc or file.model_dump()
        if not project_doc:
            return None

        project_path = project_doc.get("path")
        file_path = effective_file.path
        abs_path = await self._build_abs_file_path(
            project_path,
            file_path,
        )

        content = await self._extract_code_from_file(
            abs_path,
            None,
        )

        result = {
            "file_id": file.id,
            "file_name": file.name,
            "file_path": file.path,
            "node_type": file.node_type,
            "qname": file.qname,
            "code": content,
        }
        return result
