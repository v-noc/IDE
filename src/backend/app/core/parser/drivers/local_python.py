"""In-process Python driver: parso/jedi/libcst, implements LanguageDriver."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from app.core.parser.ast.models import BaseNode, ClassNode as ASTClassNode
from app.core.parser.ast.scanner import scan_with_meta
from app.core.parser.drivers.protocol import (
    CallFrameResult,
    FileIdResult,
    FolderIdResult,
    InitializeResult,
    ParseResult,
)
from app.core.parser.graph_builder.discovery.file_tracker import FileTracker
from app.core.parser.graph_builder.discovery.folder_tracker import FolderTracker
from app.core.parser.jedi_adapter.call_resolver.call_resolver import (
    CallFrameStack,
    CallHierarchyResolver,
)
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.jedi_adapter.resolver import MROResolver

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
        if isinstance(node, ASTClassNode):
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


class LocalPythonDriver:
    """Python parso/jedi/libcst driver running inside the backend process."""

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._jedi_manager = JediProjectManager(project_path)
        self._mro_resolver = MROResolver(self._jedi_manager)
        self._file_tracker = FileTracker()
        self._folder_tracker = FolderTracker()

    async def initialize(
        self, project_path: str, config: Optional[dict] = None
    ) -> InitializeResult:
        self._project_path = Path(project_path)
        self._jedi_manager = JediProjectManager(self._project_path)
        self._mro_resolver = MROResolver(self._jedi_manager)
        return InitializeResult(status="ok", extensions=[".py"])

    async def parse_file(
        self, file_path: str, content: str, *, resolve_mro: bool = False
    ) -> ParseResult:

        def _run() -> ParseResult:
            nodes, processed_content, modified = scan_with_meta(content, file_path)
            if resolve_mro:
                _apply_mro_to_classes(
                    nodes, file_path, processed_content, self._mro_resolver
                )
            return ParseResult(
                nodes=nodes, content=processed_content, modified=modified
            )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def resolve_calls(
        self, file_path: str, calls: List[BaseNode]
    ) -> CallFrameResult:

        def _run() -> CallFrameResult:
            merged = CallFrameStack(
                target_qname="root", target_id="root", children=[]
            )
            for call in calls:
                resolver = CallHierarchyResolver(self._jedi_manager)
                try:
                    sub = resolver.resolve_call_hierarchy(file_path, call)
                    _merge_frame_stack(merged, sub)
                except Exception:
                    logger.exception(
                        "Call resolution failed for %s in %s", call, file_path
                    )
            return CallFrameResult(call_frame_stack=merged)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def read_or_inject_file_id(self, file_path: str) -> FileIdResult:

        def _run() -> FileIdResult:
            fid, modified = self._file_tracker.process_file_detailed(Path(file_path))
            return FileIdResult(file_id=fid, modified=modified)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def read_or_inject_folder_id(self, folder_path: str) -> FolderIdResult:

        def _run() -> FolderIdResult:
            fid, modified = self._folder_tracker.ensure_tracking_detailed(
                Path(folder_path)
            )
            return FolderIdResult(folder_id=fid, modified=modified)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def shutdown(self) -> None:
        return None

    async def is_alive(self) -> bool:
        return True


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
