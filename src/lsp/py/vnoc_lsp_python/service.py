"""Core driver logic (sync); RPC layer calls these via thread pool when needed."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from vnoc_lsp_python.call_resolver import CallFrameStack, CallHierarchyResolver
from vnoc_lsp_python.file_folder_ids import read_or_inject_file_id, read_or_inject_folder_id
from vnoc_lsp_python.jedi_manager import JediProjectManager
from vnoc_lsp_python.models import BaseNode, ClassNode
from vnoc_lsp_python.mro_resolver import MROResolver
from vnoc_lsp_python.scanner import scan_with_meta

logger = logging.getLogger(__name__)


def _get_name_column(content: str, node: BaseNode) -> int:
    line_index = node.position.line - 1
    if line_index < 0:
        return node.position.column
    lines = content.splitlines()
    if line_index >= len(lines):
        return node.position.column
    line = lines[line_index]
    name_idx = line.find(node.name)
    if name_idx == -1:
        return node.position.column
    return name_idx


def _apply_mro_to_classes(
    nodes: List[BaseNode],
    file_path: str,
    content: str,
    mro_resolver: MROResolver,
) -> None:
    for node in nodes:
        if isinstance(node, ClassNode):
            try:
                name_column = _get_name_column(content, node)
                mro = mro_resolver.resolve_mro(
                    file_path=file_path,
                    source=content,
                    line=node.position.line,
                    column=name_column + len(node.name),
                )
                node.base_classes = mro
            except Exception as e:
                logger.error("Failed to resolve MRO for %s: %s", node.name, e)
                node.base_classes = []
        if node.children:
            _apply_mro_to_classes(node.children, file_path, content, mro_resolver)


def _merge_frame_stack(target: CallFrameStack, source: CallFrameStack) -> None:
    for source_child in source.children:
        matched = next(
            (c for c in target.children if c.target_id == source_child.target_id),
            None,
        )
        if not matched:
            matched = CallFrameStack(
                target_qname=source_child.target_qname,
                target_id=source_child.target_id,
                children=[],
            )
            target.add_child(matched)
        _merge_frame_stack(matched, source_child)


class PythonDriverService:
    def __init__(self) -> None:
        self._project_path: Path | None = None
        self._jedi: JediProjectManager | None = None
        self._mro: MROResolver | None = None

    def initialize(self, project_path: str, language: str = "python") -> dict:
        self._project_path = Path(project_path)
        self._jedi = JediProjectManager(self._project_path)
        self._mro = MROResolver(self._jedi)
        return {"status": "ok", "extensions": [".py"]}

    def parse_file(self, file_path: str, content: str, resolve_mro: bool) -> dict:
        if self._jedi is None or self._mro is None:
            raise RuntimeError("Driver not initialized")
        nodes, processed_content, modified = scan_with_meta(content, file_path)
        if resolve_mro:
            _apply_mro_to_classes(nodes, file_path, processed_content, self._mro)
        return {
            "nodes": [n.model_dump(mode="json") for n in nodes],
            "content": processed_content,
            "modified": modified,
        }

    def resolve_calls(self, file_path: str, calls: List[dict]) -> dict:
        if self._jedi is None:
            raise RuntimeError("Driver not initialized")
        merged = CallFrameStack(
            target_qname="root", target_id="root", children=[]
        )
        from vnoc_lsp_python.models import CallNode, ClassNode, FunctionNode

        def decode_call(d: dict) -> BaseNode:
            t = d.get("type")
            children = [decode_call(c) for c in d.get("children") or []]
            payload = {**d, "children": children}
            if t == "call":
                return CallNode.model_validate(payload)
            if t == "function":
                return FunctionNode.model_validate(payload)
            if t == "class":
                return ClassNode.model_validate(payload)
            raise ValueError(t)

        typed_calls = [decode_call(c) for c in calls]

        for call in typed_calls:
            resolver = CallHierarchyResolver(self._jedi)
            try:
                sub = resolver.resolve_call_hierarchy(file_path, call)
                _merge_frame_stack(merged, sub)
            except Exception:
                logger.exception("resolve_calls failed for one call site")

        return {"call_frame_stack": merged.to_json_tree()}

    def read_or_inject_file_id(self, file_path: str) -> dict:
        fid, modified = read_or_inject_file_id(Path(file_path))
        return {"file_id": fid, "modified": modified}

    def read_or_inject_folder_id(self, folder_path: str) -> dict:
        fid, modified = read_or_inject_folder_id(Path(folder_path))
        return {"folder_id": fid, "modified": modified}
