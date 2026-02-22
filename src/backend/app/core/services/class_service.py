import aiofiles

from datetime import datetime, timezone
from typing import Literal, Optional

from app.core.repository import Repositories
from app.core.model.nodes import ClassNode
from app.core.model.properties import CodePosition
from app.core.model.nodes import ProjectNode
from app.core.utils.code_utils import build_abs_file_path, extract_code_from_file


class ClassService():
    def __init__(self, repos: Repositories, project: ProjectNode):
        self.repos = repos
        self.project = project

    async def create(
        self,
        id: str,
        name: str,
        qname: str,
        description: str,
        position: CodePosition,
        base_classes: Optional[set] = None,
        branch_name: Optional[str] = None,
    ):
        class_node = ClassNode(
            id=id,
            name=name,
            qname=qname,
            description=description,
            base_classes=base_classes or set(),
            code_position=position,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.repos.class_repo.create(class_node, self.project.db_name, branch_name=branch_name)

    async def get(self, class_id: str, branch_name: Optional[str] = None):
        return await self.repos.class_repo.get_by_id(
            class_id, self.project.db_name, branch_name=branch_name
        )

    async def update(self, class_node: ClassNode, branch_name: Optional[str] = None):
        return await self.repos.class_repo.update(
            class_node, self.project.db_name, branch_name=branch_name
        )

    async def delete(self, class_id: str, branch_name: Optional[str] = None):
        return await self.repos.class_repo.delete(
            class_id, self.project.db_name, branch_name=branch_name
        )

    async def add_child(
        self,
        parent_class_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
        branch_name: Optional[str] = None,
    ):
        return await self.repos.class_repo.move_item(
            parent_class_id, item_id, item_type, self.project.db_name, branch_name=branch_name
        )

    async def add_function(self, parent_class_id: str, function_id: str, branch_name: Optional[str] = None):
        return await self.add_child(parent_class_id, function_id, "function", branch_name=branch_name)

    async def add_call(self, parent_class_id: str, call_id: str, branch_name: Optional[str] = None):
        return await self.add_child(parent_class_id, call_id, "call", branch_name=branch_name)

    async def add_class(self, parent_class_id: str, class_id: str, branch_name: Optional[str] = None):
        return await self.add_child(parent_class_id, class_id, "class", branch_name=branch_name)

    async def move_item(
        self,
        new_parent_id: str,
        item_id: str,
        item_type: Literal[
            "function", "class", "call", "code_element_group", "call_group"
        ],
        branch_name: Optional[str] = None,
    ):
        return await self.repos.class_repo.move_item(
            new_parent_id, item_id, item_type, self.project.db_name, branch_name=branch_name
        )

    async def get_children(
        self, class_id: str, child_type: Optional[list[str]] = None, branch_name: Optional[str] = None
    ):
        return await self.repos.class_repo.get_children(
            class_id, child_type or [], self.project.db_name, branch_name=branch_name
        )

    async def get_code(self, class_id: str, branch_name: Optional[str] = None):
        class_node = await self.get(class_id)
        if not class_node:
            return None

        parent_file = await self.repos.file_repo.get_parent_file(
            class_id, self.project.db_name, branch_name=branch_name
        )
        if not parent_file:
            return None

        abs_path = build_abs_file_path(self.project.path, parent_file.path)
        code = await extract_code_from_file(abs_path, class_node.code_position)

        result = {
            "id": class_node.id,
            "name": class_node.name,
            "qname": class_node.qname,
            "file_path": parent_file.path,
            "file_name": parent_file.name,
            "code": code,
        }
        result["position"] = class_node.code_position.model_dump()
        return result

    async def write_code(
        self, class_id: str, code_block: str, branch_name: Optional[str] = None
    ) -> dict:
        """Write code for a class at its position. Returns {success: bool, error?: str}."""
        class_node = await self.get(class_id, branch_name=branch_name)
        if not class_node:
            return {"success": False, "error": "Class not found"}

        parent_file = await self.repos.file_repo.get_parent_file(
            class_id, self.project.db_name
        )
        if not parent_file:
            return {"success": False, "error": "Enclosing file not found"}

        abs_path = build_abs_file_path(self.project.path, parent_file.path)
        position = class_node.code_position

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                content = await f.read()

            lines = content.splitlines(True)
            start_line = max(1, position.line_no) - 1
            end_line = position.end_line_no
            start_col = max(0, position.col_offset)
            end_col = position.end_col_offset

            prefix = lines[start_line][:start_col] if 0 <= start_line < len(lines) else ""
            new_lines = [
                (prefix + l if i > 0 else (prefix + l))
                for i, l in enumerate(code_block.splitlines(True))
            ]

            if end_line is None:
                lines[start_line:] = new_lines
            else:
                tail = ""
                if 0 <= (end_line - 1) < len(lines) and end_col is not None:
                    original = lines[end_line - 1]
                    tail = original[end_col:]
                lines[start_line:end_line] = new_lines
                if tail:
                    lines.insert(start_line + len(new_lines), tail)

            async with aiofiles.open(abs_path, "w", encoding="utf-8") as f:
                await f.writelines(lines)
            return {"success": True}
        except IOError as e:
            return {"success": False, "error": str(e)}
