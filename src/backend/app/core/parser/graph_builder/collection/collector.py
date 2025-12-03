import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.core.model.nodes import ProjectNode
from app.core.parser.ast.scanner import scan
from app.core.parser.jedi_adapter.manager import JediProjectManager
from app.core.parser.jedi_adapter.resolver import MROResolver
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel

from .ast_processor import ASTProcessor
from .hierarchy import HierarchyBuilder, FolderChange

logger = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    file_scope: ScopeModel
    removed_scope_ids: List[str]  # IDs of scopes that were deleted
    folder_changes: List[FolderChange]


class Collector:
    def __init__(
        self,
        project_node: ProjectNode,
        scope_manager: ScopeManager,
        jedi_manager: JediProjectManager,
    ):
        self.project_node = project_node
        self.project_path = Path(project_node.path)
        self.manager = scope_manager
        self.jedi_manager = jedi_manager

        self.hierarchy_builder = HierarchyBuilder(project_node, scope_manager)
        self.mro_resolver = MROResolver(jedi_manager)
        self.ast_processor = ASTProcessor(scope_manager, self.mro_resolver)

    def reset_session(self) -> None:
        """Reset builder caches between orchestrator runs."""
        self.hierarchy_builder.reset_session()

    def process_file(
        self, file_path: str, checksum: str
    ) -> Optional[CollectionResult]:
        """
        Process a single file for Phase 1 collection.

        For NEW files:
        - Create folder hierarchy and file scope
        - Parse AST and create all scopes
        - Return all scopes as updated (new) for Phase 2

        For UPDATED files:
        - Build folder hierarchy and update file scope if needed
        - Parse AST and build current scope hierarchy
        - For each scope found by ID, check if path/position/name changed
        - Create new scopes
        - Track removed scopes (by ID)
        - Return only new or modified scopes for Phase 2

        Returns:
        - file_scope: The file scope node
        - updated_scopes: New or modified scopes (need Phase 2 body analysis)
        - removed_scope_ids: IDs of deleted scopes
        """
        abs_path = Path(file_path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.error(
                "File %s is not inside project path %s",
                file_path,
                self.project_path,
            )
            return None
        # 1. Build Hierarchy (creates/updates file, folder scopes)
        build_result = self.hierarchy_builder.build_hierarchy(
            rel_path, checksum)
        if not build_result:
            logger.error(f"Failed to build hierarchy for {file_path}")
            return None
        file_scope = build_result.scope

        # 2. Parse Content & Scan AST
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            ast_nodes = scan(content, str(abs_path))
        except Exception as e:
            logger.error(f"Failed to scan AST for {file_path}: {e}")
            return None
        # 3. Get existing children from database (recursively collect all
        # descendants)
        existing_map = self._collect_all_descendant_scopes(file_scope.id)

        # 4. Process AST Nodes to build current scope hierarchy
        # ASTProcessor will check each scope by ID and update if path/pos/name
        # changed
        current_scopes_nodes = self.ast_processor.process_ast_nodes(
            ast_nodes, file_scope, content)
        # 5. Determine which scopes are new or modified (Internal Update)
        # We still need to iterate to find removed scopes and update DB
        current_ids = set()

        for scope, node in current_scopes_nodes:
            current_ids.add(scope.id)

            existing = existing_map.get(scope.id)
            if not existing:
                # New scope - already created by ASTProcessor
                logger.debug(f"New scope detected: {scope.qname}")
            else:
                # Existing scope - check if it changed
                if self._scope_changed(existing, scope):
                    # Modified scope - already updated by ASTProcessor
                    logger.debug(f"Modified scope detected: {scope.qname}")

        # 6. Identify removed scopes (existed before but not in current AST)
        removed_scope_ids = []
        for child_id in existing_map.keys():
            if child_id not in current_ids:
                removed_scope_ids.append(child_id)
                logger.info(
                    f"Scope removed: {existing_map[child_id].qname} "
                    f"(ID: {child_id})")
        logger.info(
            f"File {file_path}: {len(removed_scope_ids)} scopes removed")

        return CollectionResult(
            file_scope=file_scope,
            removed_scope_ids=removed_scope_ids,
            folder_changes=build_result.folder_changes,
        )

    def process_folder(self, folder_path: str) -> Optional[List[FolderChange]]:
        """Ensure folder hierarchy exists for a folder change event."""
        abs_path = Path(folder_path)
        try:
            rel_path = abs_path.relative_to(self.project_path)
        except ValueError:
            logger.error(
                "Folder %s is not inside project path %s",
                folder_path,
                self.project_path,
            )
            return None
        build_result = self.hierarchy_builder.ensure_folder(rel_path)
        if not build_result:
            return None
        return build_result.folder_changes

    def _collect_all_descendant_scopes(
        self, parent_scope_id: str
    ) -> dict[str, ScopeModel]:  # noqa: E501
        """
        Recursively collect all descendant scopes from a parent scope.
        Returns a dictionary mapping scope ID to ScopeModel.
        """
        result = {}
        queue = [parent_scope_id]

        while queue:
            current_id = queue.pop(0)
            children = self.manager.get_children(current_id)
            for child in children:
                if child.id not in result:
                    result[child.id] = child
                    queue.append(child.id)

        return result

    def _scope_changed(
        self, existing: ScopeModel, current: ScopeModel
    ) -> bool:
        """
        Check if a scope has changed by comparing key attributes.
        Checks: checksum, position, name, qname (path).
        """
        return (
            existing.checksum != current.checksum or
            existing.start_line != current.start_line or
            existing.start_col != current.start_col or
            existing.end_line != current.end_line or
            existing.end_col != current.end_col or
            existing.name != current.name or
            existing.qname != current.qname
        )
