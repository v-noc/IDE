import logging
from typing import Optional
from pathlib import Path

from arango.database import StandardDatabase

from app.core.model.nodes import ProjectNode
from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.scope_manager.models import ScopeModel
from app.core.parser.graph_builder.discovery.scanner import (
    FileScanner,
    ScanResult,
)
from app.core.parser.graph_builder.discovery.change_detector import (
    ChangeDetector,
    ChangeSet,
)

from app.core.parser.graph_builder.collection.collector import Collector
from app.core.parser.graph_builder.collection.hierarchy import FolderChange
from app.core.parser.graph_builder.analysis.body_parser import BodyParser
from app.core.parser.graph_builder.sync.graph_sync import (
    MainGraphSyncService,
)
from app.core.repository import Repositories
import time


logger = logging.getLogger(__name__)


class GraphBuilderOrchestrator:
    def __init__(
        self,
        project_node: ProjectNode,
        db: Optional[StandardDatabase] = None,
        scope_manager: Optional[ScopeManager] = None,
        ignore_file_name: str = ".gitignore",
    ):
        self.project_node = project_node
        self.project_path = project_node.path
        self.project_root = Path(self.project_path)
        # Main ArangoDB connection (optional for now)
        self.db = db

        # Initialize ScopeManager
        # Note: ScopeManager handles DB connection internally
        self.scope_manager = scope_manager or ScopeManager(project_node.name)

        # Initialize Jedi Adapter
        from app.core.parser.jedi_adapter.manager import JediProjectManager

        self.jedi_manager = JediProjectManager(self.project_root)

        # Initialize Discovery components
        self.file_scanner = FileScanner(
            self.project_path,
            ignore_file_name=ignore_file_name,
        )
        self.change_detector = ChangeDetector(self.scope_manager)

        # Initialize Collection components
        self.collector = Collector(
            self.project_node,
            self.scope_manager,
            self.jedi_manager,
        )

        # Initialize Analysis components
        self.body_parser = BodyParser(
            self.project_path,
            self.project_node.name,
            self.scope_manager,
            self.jedi_manager
        )

        # Initialize Sync components
        # Will create sync service with version when needed in _process_changes

        self.repos = Repositories(self.db) if self.db else None
        self._pending_folder_changes: list[FolderChange] = []

    def resync(self) -> ChangeSet:
        """
        Perform an incremental resync of the project.
        1. Scan files
        2. Detect changes
        3. Phase 1: Structure Collection (Scopes)
        4. Phase 2: Body Analysis (Calls)
        """
        logger.info(
            "Starting resync for project: %s",
            self.project_node.name,
        )

        # 1. Scan Disk
        scan_result = self.file_scanner.scan()
        logger.info(
            "Scanned %d files across %d folders on disk",
            len(scan_result.files),
            len(scan_result.folders),
        )

        # 2. Detect Changes
        change_set = self.change_detector.detect_changes(scan_result)
        logger.info(f"Detected changes: {change_set}")

        if (not change_set.has_changes() and
                not change_set.has_folder_changes()):
            logger.info("No changes detected. Graph is up to date.")
            return change_set

        # 3. Process Changes (Phase 1 & 2)
        self._process_changes(change_set, scan_result)

        return change_set

    def _process_changes(self, change_set: ChangeSet, scan_result: ScanResult):
        """
        Process the detected changes in two phases.
        """
        self.collector.reset_session()
        files_to_process = change_set.new_files + change_set.modified_files

        collection_results = []
        folder_changes = []
        touched_folder_ids = set()

        # Handle folder additions proactively to ensure hierarchy exists
        for folder_path in change_set.new_folders:
            folder_result = self.collector.process_folder(folder_path)
            if folder_result:
                folder_changes.extend(folder_result)
                touched_folder_ids.update(fc.scope.id for fc in folder_result)

        # Phase 1: Collection (Structure)
        logger.info("Starting Phase 1: Collection")
        for file_path in files_to_process:
            checksum = scan_result.files.get(file_path)
            if checksum:
                logger.info(f"Collecting structure for: {file_path}")
                result = self.collector.process_file(file_path, checksum)
                if result:
                    collection_results.append(result)
                    folder_changes.extend(result.folder_changes)
                    touched_folder_ids.update(
                        fc.scope.id for fc in result.folder_changes)

        # Phase 2: Analysis (Bodies)
        logger.info("Starting Phase 2: Analysis")
        for result in collection_results:
            logger.info(
                "Analyzing changes for: %s",
                result.file_scope.file_path,
            )

            # 1. Delete Removed Scopes
            for scope_id in result.removed_scope_ids:
                logger.info(f"Deleting removed scope ID: {scope_id}")
                self.scope_manager.delete_scope(scope_id)

            # 2. Process File Body (Full Analysis)
            # We process the entire file AST every time it changes
            logger.info("Processing file body: %s", result.file_scope.qname)

            # Clear file-scope calls; children clear during traversal
            self.scope_manager.clear_calls(result.file_scope.id)

            # Parse the full AST tree
            # BodyParser traverses descendants and clears their calls en route
            self.body_parser.process_ast(result.file_scope)

        # Debugger: Visualize scope and call site graph
        # self._print_call_site_tree()
        # self._visualize_graph()

        # Process Deleted folders before files to avoid orphan references
        for folder_path in change_set.deleted_folders:
            logger.info(f"Processing folder deletion: {folder_path}")
            self._handle_folder_deletion(
                folder_path, folder_changes, touched_folder_ids)

        # Process Deleted files (Full file deletion)
        for file_path in change_set.deleted_files:
            logger.info(f"Processing file deletion: {file_path}")
            self._handle_file_deletion(
                file_path, folder_changes, touched_folder_ids)

        # Phase 3: Sync scopes to graph database
        # Generate version at project level
        sync_version = int(time.time_ns())
        if self.repos:
            sync_service = MainGraphSyncService(
                self.repos,
                self.scope_manager,
                self.project_node,
                sync_version
            )

            sync_service.sync_scope_hierarchy(self.project_node.id)
        else:
            logger.warning("No database connection for sync; skipping")

        logger.info("Folder changes prepared for sync: %d",
                    len(folder_changes))
        self._pending_folder_changes = folder_changes

    def _handle_folder_deletion(
        self,
        folder_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        folder_scope = self._scope_from_path(folder_path, is_file=False)
        if not folder_scope:
            logger.warning(
                "Folder scope not found for deletion path: %s", folder_path)
            return

        self._append_folder_change(
            folder_changes, touched_folder_ids, folder_scope, "deleted"
        )
        self.scope_manager.delete_scope(folder_scope.id)

    def _handle_file_deletion(
        self,
        file_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:

        self.scope_manager.delete_file_scope(file_path)
        self._touch_parent_folders(
            file_path, folder_changes, touched_folder_ids)

    def _touch_parent_folders(
        self,
        target_path: str,
        folder_changes: list,
        touched_folder_ids: set,
    ) -> None:
        try:
            rel_path = Path(target_path).relative_to(self.project_root)
        except ValueError:
            logger.warning("Path %s is outside project root %s",
                           target_path, self.project_root)
            return

        folder_parts = rel_path.parts[:-1]
        if not folder_parts:
            return

        current_qname = self.project_node.name

        for part in folder_parts:
            current_qname = f"{current_qname}.{part}"
            folder_scope = self.scope_manager.get_scope_by_qname(current_qname)
            if not folder_scope or folder_scope.id in touched_folder_ids:
                continue
            self._append_folder_change(
                folder_changes, touched_folder_ids, folder_scope, "updated"
            )

    def _append_folder_change(
        self,
        folder_changes: list,
        touched_folder_ids: set,
        scope: Optional[ScopeModel],
        action: str,
    ) -> None:
        if not scope or scope.id in touched_folder_ids:
            return
        folder_changes.append(
            FolderChange(scope=scope, action=action)
        )
        touched_folder_ids.add(scope.id)

    def _scope_from_path(
        self, abs_path: str, is_file: bool
    ) -> Optional[ScopeModel]:
        """
        Resolve a scope using a filesystem path by mapping to its qname.
        """
        try:
            rel_path = Path(abs_path).relative_to(self.project_root)
        except ValueError:
            logger.warning(
                "Path %s is outside project root %s",
                abs_path,
                self.project_root
            )
            return None

        parts = list(rel_path.parts)
        if not parts:
            return self.scope_manager.get_scope_by_qname(
                self.project_node.name
            )

        if is_file and parts:
            parts[-1] = Path(parts[-1]).stem

        qname = ".".join([self.project_node.name] + parts)
        return self.scope_manager.get_scope_by_qname(qname)

    def _visualize_graph(self):
        """
        Visualize the scope and call site graph using pyvis.
        Creates an interactive HTML visualization showing:
        - Scope hierarchy (CONTAINS relationships)
        - Call sites and their relationships
          (HAS_CALL_SITE, TARGETS, NEXT_IN_CHAIN)
        """
        try:
            from pyvis.network import Network
        except ImportError:
            logger.warning(
                "pyvis not installed. Skipping graph visualization."
            )
            return

        # Create network graph
        net = Network(
            height="800px",
            width="100%",
            bgcolor="#222222",
            font_color="white",
            directed=True,
        )

        # Configure physics for better layout
        net.set_options("""
        {
            "physics": {
                "hierarchicalRepulsion": {
                    "centralGravity": 0.0,
                    "springLength": 200,
                    "springConstant": 0.01,
                    "nodeDistance": 200,
                    "damping": 0.09
                },
                "maxVelocity": 50,
                "minVelocity": 0.75,
                "solver": "hierarchicalRepulsion",
                "stabilization": {"iterations": 200}
            }
        }
        """)

        # Color mapping for scope types
        scope_type_colors = {
            "folder": "#4A90E2",    # Blue
            "file": "#50C878",      # Green
            "class": "#FF6B6B",     # Red
            "function": "#FFD93D",  # Yellow
        }

        # Get all scopes
        scopes = self.scope_manager.get_all_scopes()
        scope_ids = {scope.id for scope in scopes}

        # Add scope nodes
        for scope in scopes:
            color = scope_type_colors.get(scope.type.value, "#888888")
            label = f"{scope.name}\n({scope.type.value})\n{scope.qname}"
            title = (
                f"ID: {scope.id}\n"
                f"Name: {scope.name}\n"
                f"QName: {scope.qname}\n"
                f"Type: {scope.type.value}\n"
                f"File: {scope.file_path}\n"
                f"Lines: {scope.start_line}-{scope.end_line}"
            )
            net.add_node(
                scope.id,
                label=label,
                title=title,
                color=color,
                shape="box",
                font={"size": 10},
            )

        # Get all CONTAINS relationships (scope hierarchy)
        contains_edges = self.scope_manager.repository.conn.execute(
            """
            MATCH (parent:Scope)-[:CONTAINS]->(child:Scope)
            RETURN parent.id AS parent_id, child.id AS child_id
            """
        )
        for row in contains_edges:
            parent_id, child_id = row[0], row[1]
            if parent_id in scope_ids and child_id in scope_ids:
                net.add_edge(
                    parent_id,
                    child_id,
                    color="#888888",
                    label="CONTAINS",
                    arrows="to",
                )

        # Get all call sites
        call_sites_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite)
            RETURN cs.id AS cs_id, cs.line AS line, cs.col AS col,
                   cs.name AS name
            """
        )

        call_site_ids = set()
        for row in call_sites_query:
            cs_id, line, col, name = row
            call_site_ids.add(cs_id)

            # Add call site node
            label = f"CallSite\n{name or 'unknown'}\nL{line}:C{col}"
            title = (
                f"CallSite ID: {cs_id}\n"
                f"Name: {name or 'unknown'}\n"
                f"Line: {line}, Col: {col}"
            )
            net.add_node(
                cs_id,
                label=label,
                title=title,
                color="#FFA500",  # Orange for call sites
                shape="diamond",
                font={"size": 9},
            )

        # Get HAS_CALL_SITE relationships (caller -> call site)
        has_call_site_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (caller:Scope)-[:HAS_CALL_SITE]->(cs:CallSite)
            RETURN caller.id AS caller_id, cs.id AS cs_id
            """
        )
        for row in has_call_site_query:
            caller_id, cs_id = row[0], row[1]
            if caller_id in scope_ids and cs_id in call_site_ids:
                net.add_edge(
                    caller_id,
                    cs_id,
                    color="#00FF00",  # Green
                    label="HAS_CALL_SITE",
                    arrows="to",
                )

        # Get TARGETS relationships (call site -> callee)
        targets_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite)-[:TARGETS]->(callee:Scope)
            RETURN cs.id AS cs_id, callee.id AS callee_id
            """
        )
        for row in targets_query:
            cs_id, callee_id = row[0], row[1]
            if cs_id in call_site_ids and callee_id in scope_ids:
                net.add_edge(
                    cs_id,
                    callee_id,
                    color="#FF00FF",  # Magenta
                    label="TARGETS",
                    arrows="to",
                )

        # Get NEXT_IN_CHAIN relationships (call site -> next call site)
        next_in_chain_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite)-[:NEXT_IN_CHAIN]->(next:CallSite)
            RETURN cs.id AS cs_id, next.id AS next_id
            """
        )
        for row in next_in_chain_query:
            cs_id, next_id = row[0], row[1]
            if cs_id in call_site_ids and next_id in call_site_ids:
                net.add_edge(
                    cs_id,
                    next_id,
                    color="#00FFFF",  # Cyan
                    label="NEXT_IN_CHAIN",
                    arrows="to",
                    dashes=True,
                )

        # Save visualization to HTML file
        output_path = "graph_visualization.html"
        net.save_graph(str(output_path))
        logger.info(f"Graph visualization saved to: {output_path}")

    def _print_call_site_tree(self):
        """
        Print call chain tree: root call sites -> chain.
        Simple: show root calls (no incoming NEXT_IN_CHAIN) and their chains.
        """
        # Get all root call sites (no incoming NEXT_IN_CHAIN)
        root_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite)
            WHERE NOT EXISTS {
                MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(cs)
            }
            RETURN cs.id AS cs_id, cs.line AS line, cs.col AS col,
                   cs.name AS name
            ORDER BY cs.line, cs.col
            """
        )

        root_calls = []
        for row in root_query:
            root_calls.append({
                "id": row[0],
                "line": row[1],
                "col": row[2],
                "name": row[3],
            })

        if not root_calls:
            print("No root call sites found.")
            return

        print("\n" + "=" * 80)
        print("CALL CHAIN TREE")
        print("=" * 80)

        visited = set()
        for i, root_call in enumerate(root_calls):
            is_last = i == len(root_calls) - 1
            if root_call["id"] not in visited:
                self._print_call_site_node(
                    root_call["id"],
                    indent=0,
                    visited=visited,
                    is_last=is_last,
                )

        print("\n" + "=" * 80 + "\n")

    def _print_call_site_node(
        self,
        call_site_id: str,
        indent: int = 0,
        visited: set = None,
        is_last: bool = False,
    ):
        """
        Recursively print a call site node and its children in tree form.

        Args:
            call_site_id: ID of the call site to print
            indent: Current indentation level
            visited: Set of visited call site IDs to avoid cycles
        """
        if visited is None:
            visited = set()

        # Check if already printed (avoid duplicates)
        if call_site_id in visited:
            return
        visited.add(call_site_id)

        # Get call site details
        cs_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite {id: $cs_id})
            RETURN cs.id AS id, cs.line AS line, cs.col AS col,
                   cs.name AS name
            """,
            {"cs_id": call_site_id},
        )

        cs_data = None
        for row in cs_query:
            cs_data = {
                "id": row[0],
                "line": row[1],
                "col": row[2],
                "name": row[3],
            }
            break

        if not cs_data:
            return

        # Get callee scope (target)
        callee_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (cs:CallSite {id: $cs_id})-[:TARGETS]->(callee:Scope)
            RETURN callee.id AS id, callee.name AS name, callee.qname AS qname,
                   callee.type AS type, callee.file_path AS file_path
            """,
            {"cs_id": call_site_id},
        )

        callee_info = None
        for row in callee_query:
            callee_info = {
                "id": row[0],
                "name": row[1],
                "qname": row[2],
                "type": row[3],
                "file_path": row[4],
            }
            break

        # Get children in chain (NEXT_IN_CHAIN relationships)
        children = self.scope_manager.get_call_chain_children(call_site_id)

        # Build prefix for indentation
        prefix = "  " * indent

        call_name = cs_data["name"] or "unknown"
        line_col = f"L{cs_data['line']}:C{cs_data['col']}"

        callee_str = ""
        if callee_info:
            file_name = Path(callee_info["file_path"]).name
            callee_str = (
                f" -> [{callee_info['type']}] {callee_info['name']} "
                f"({file_name})"
            )

        # Determine tree connector
        if indent == 0:
            tree_char = "┌─"
        elif children:
            tree_char = "├─"
        else:
            tree_char = "└─"

        # Print call site
        print(f"{prefix}{tree_char} {call_name} {line_col}{callee_str}")

        # Print chain continuation (NEXT_IN_CHAIN)
        if children:
            for i, child in enumerate(children):
                child_cs = child["call_site"]
                is_last_child = i == len(children) - 1
                # Only print if not already visited
                if child_cs.id not in visited:
                    self._print_call_site_node(
                        child_cs.id,
                        indent=indent + 1,
                        visited=visited,
                        is_last=is_last and is_last_child,
                    )
