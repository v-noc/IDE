import aiofiles

from datetime import datetime, timezone
from typing import Any, Literal, Optional, Tuple

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import FunctionNode, ClassNode
from app.core.model.properties import CodePosition
from app.core.utils.code_utils import (
    build_abs_file_path,
    extract_code_from_content,
    extract_code_from_file,
)

from app.db.context import ProjectUoW


def _lineage_docs_as_spine_flat(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Force a single-child chain so TreeBuilder yields one nested spine (no sibling payload)."""
    flat: list[dict[str, Any]] = []
    for i, d in enumerate(docs):
        out = dict(d)
        next_id = None
        if i + 1 < len(docs):
            nxt = docs[i + 1]
            next_id = nxt.get("@id") or nxt.get("id")
        out["children"] = [next_id] if next_id else []
        flat.append(out)
    return flat


class CodeElementService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

    async def create(self, node: FunctionNode | ClassNode):
        return await self.repos.code_element_repo.create(node)

    async def get(self, node_id: str):
        return await self.repos.code_element_repo.get_by_id(node_id)

    async def update(self, node: FunctionNode | ClassNode):
        return await self.repos.code_element_repo.update(node)

    async def delete(self, node_id: str):
        return await self.repos.code_element_repo.delete(node_id)

    async def get_children(self, node_id: str):
        return await self.repos.code_element_repo.get_children(node_id, [])

    async def get_target_lineage_tree(
        self, target_id: str, *, compare_to: bool = False
    ) -> dict[str, Any]:
        """Root→leaf document chain as path ids and nested tree (spine only)."""
        repos = (
            self.uow.get_project_repos(use_compare_to=True)
            if compare_to
            else self.repos
        )
        docs = await repos.code_element_repo.get_node_lineage(target_id)
        if not docs:
            return {"path_ids": [], "tree": []}

        tree_builder = TreeBuilder(docs)
        tree = tree_builder.build()

        path_ids: list[str] = []

        def collect_path_ids(node):
            if node.id:
                path_ids.append(node.id)
            for child in node.children:
                collect_path_ids(child)
        for node in tree:
            collect_path_ids(node)

        return {
            "path_ids": path_ids,
            "tree": [n.model_dump(mode="json") for n in tree],
        }

    async def get_code_descendants(
        self,
        parent_id: str,
        child_types: list[str],
        depth_start: int | None = None,
        depth_max: int | None = None,
        compare_to: bool = False,
    ) -> Tuple[list[Any], dict[str, dict[str, Any]]]:
        repos = (
            self.uow.get_project_repos(use_compare_to=True)
            if compare_to
            else self.repos
        )
        return await repos.code_element_repo.get_code_descendant_nodes(
            parent_id,
            child_types,
            depth_start=depth_start,
            depth_max=depth_max,
        )

    async def add_child(self, parent_node_id: str, child_node_id: str, child_type: Literal["function", "class", "call", "code_element_group", "call_group"]):
        return await self.repos.code_element_repo.move_item(parent_node_id, child_node_id, child_type)

    async def get_code(self, code_element_id: str, compare_to: Optional[bool] = False):

        current_repos = self.repos
        if compare_to:
            current_repos = self.uow.get_project_repos(use_compare_to=True)
        code_position = None
        if code_element_id.startswith("FileSchema"):
            parent_file = await current_repos.structure_repo.get_parent_file(
                code_element_id
            )
            code_element = parent_file
        else:
            code_element = await current_repos.code_element_repo.get_by_id(code_element_id)

            if not code_element:
                return None

            parent_file = await current_repos.structure_repo.get_parent_file(
                code_element_id
            )
            code_position = code_element.code_position

        if not parent_file:
            return None

        abs_path = build_abs_file_path(self.uow.project.path, parent_file.path)
        content_id = f"CodeContentSchema/{parent_file.id.replace('/', '_')}"
        # try:
        #     code = await extract_code_from_file(abs_path, code_position)

        # except OSError:
        # File not found on disk; fall back to CodeContent in DB

        try:
            content_doc = await current_repos.client.get_document(content_id)

        except Exception:
            return None
        if not content_doc or "content" not in content_doc:
            return None
        code = extract_code_from_content(
            content_doc["content"], code_position
        )

        result = {
            "id": code_element.id,
            "name": code_element.name,
            "qname": code_element.qname,
            "file_path": parent_file.path,
            "content_id": content_id,
            "file_name": parent_file.name,
            "code": code,
        }
        result["position"] = code_position.model_dump(
        ) if code_position else None
        return result

    async def write_code(self, code_element_id: str, code_block: str) -> dict:
        """Write code for a code element at its position. Returns {success: bool, error?: str}."""

        if code_element_id.startswith("FileSchema"):
            parent_file = await self.repos.structure_repo.get_parent_file(
                code_element_id
            )
            if not parent_file:
                return {"success": False, "error": "Enclosing file not found"}
            abs_path = build_abs_file_path(
                self.uow.project.path, parent_file.path)
            try:
                async with aiofiles.open(abs_path, "w", encoding="utf-8") as f:
                    await f.write(code_block)
                return {"success": True}
            except IOError as e:
                return {"success": False, "error": str(e)}

        code_element = await self.get(code_element_id)
        if not code_element:
            return {"success": False, "error": "Code element not found"}
        parent_file = await self.repos.structure_repo.get_parent_file(
            code_element_id
        )
        if not parent_file:
            return {"success": False, "error": "Enclosing file not found"}
        position = code_element.code_position
        abs_path = build_abs_file_path(self.uow.project.path, parent_file.path)

        try:
            async with aiofiles.open(abs_path, "r", encoding="utf-8") as f:
                content = await f.read()

            lines = content.splitlines(True)
            start_line = max(1, position.line_no) - 1
            end_line = position.end_line_no
            start_col = max(0, position.col_offset)
            end_col = position.end_col_offset

            prefix = lines[start_line][:start_col] if 0 <= start_line < len(
                lines) else ""
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
