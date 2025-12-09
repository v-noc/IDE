"""Visualization and debugging utilities for the graph."""
import logging
from pathlib import Path
from typing import Optional, Set

from app.core.parser.scope_manager.manager import ScopeManager

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Visualizes the scope and call site graph."""

    def __init__(self, scope_manager: ScopeManager):
        self.scope_manager = scope_manager

    def visualize_graph(self, output_path: str = "graph_visualization.html"):
        """
        Visualize the scope and call site graph using pyvis.
        Creates an interactive HTML visualization showing:
        - Scope hierarchy (CONTAINS relationships)
        - Call sites and their relationships
          (HAS_CALL_SITE, TARGETS, NEXT_IN_CHAIN)

        Args:
            output_path: Path to save the HTML visualization
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
            "folder": "#4A90E2",  # Blue
            "file": "#50C878",  # Green
            "class": "#FF6B6B",  # Red
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
        net.save_graph(str(output_path))
        logger.info(f"Graph visualization saved to: {output_path}")


class CallSiteTreePrinter:
    """Prints call chain trees for debugging."""

    def __init__(self, scope_manager: ScopeManager):
        self.scope_manager = scope_manager

    def print_call_site_tree(self):
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
            root_calls.append(
                {
                    "id": row[0],
                    "line": row[1],
                    "col": row[2],
                    "name": row[3],
                }
            )

        if not root_calls:
            print("No root call sites found.")
            return

        print("\n" + "=" * 80)
        print("CALL CHAIN TREE")
        print("=" * 80)

        visited: Set[str] = set()
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
        visited: Optional[Set[str]] = None,
        is_last: bool = False,
    ):
        """
        Recursively print a call site node and its children in tree form.

        Args:
            call_site_id: ID of the call site to print
            indent: Current indentation level
            visited: Set of visited call site IDs to avoid cycles
            is_last: Whether this is the last node at this level
        """
        if visited is None:
            visited = set()

        # Check if already printed (avoid duplicates)
        if call_site_id in visited:
            return
        visited.add(call_site_id)

        # Get call site details with caller scope
        cs_query = self.scope_manager.repository.conn.execute(
            """
            MATCH (caller:Scope)-[:HAS_CALL_SITE]->(cs:CallSite {id: $cs_id})
            RETURN cs.id AS id, cs.line AS line, cs.col AS col,
                   cs.name AS name, caller.qname AS caller_qname,
                   caller.name AS caller_name
            """,
            {"cs_id": call_site_id},
        )

        cs_data = None
        caller_info = None
        for row in cs_query:
            cs_data = {
                "id": row[0],
                "line": row[1],
                "col": row[2],
                "name": row[3],
            }
            caller_info = {
                "qname": row[4],
                "name": row[5],
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

        # Build caller info string
        caller_str = ""
        if caller_info:
            caller_str = f"[{caller_info['qname']}] "

        # Build callee info string with qualified name
        callee_str = ""
        if callee_info:
            file_name = Path(callee_info["file_path"]).name
            callee_str = (
                f" -> [{callee_info['type']}] {callee_info['name']} "
                f"({callee_info['qname']}) [{file_name}]"
            )
        else:
            callee_str = " -> [unresolved]"

        # Determine tree connector
        if indent == 0:
            tree_char = "┌─"
        elif children:
            tree_char = "├─"
        else:
            tree_char = "└─"

        # Print call site with qualified names
        print(f"{prefix}{tree_char} {caller_str}{call_name} {line_col}{callee_str}")

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

