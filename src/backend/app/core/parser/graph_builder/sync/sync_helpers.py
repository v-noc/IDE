import logging
import time
from typing import Optional

from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.repository import Repositories
from app.core.model.base import BaseNode

logger = logging.getLogger(__name__)

# Performance tracking (shared with call_sync)
_timings = {}  # noqa: E501


class SyncHelpers:
    """Helper methods for graph synchronization."""

    def __init__(self, repos: Repositories, sync_version: int):
        self.repos = repos
        self.sync_version = sync_version
        self.node_cache = {}
        _timings.clear()

    def get_graph_node_for_scope(
        self, scope: ScopeModel
    ) -> Optional[BaseNode]:
        """
        Resolve the graph node corresponding to a given scope.

        Args:
            scope: The scope to resolve

        Returns:
            The corresponding graph node or None
        """
        if scope.id in self.node_cache:
            return self.node_cache[scope.id]

        node = None
        if scope.type == ScopeType.FILE:
            node = self.repos.file_repo.find_one({"qname": scope.qname})
        elif scope.type == ScopeType.CLASS:
            node = self.repos.class_repo.find_one({"qname": scope.qname})
        elif scope.type == ScopeType.FUNCTION:
            node = self.repos.function_repo.find_one({"qname": scope.qname})
        if node:
            self.node_cache[scope.id] = node

        return node

    def create_or_update_node(
        self, repo, node, scope_id: Optional[str] = None
    ):
        """
        Create a new node or update existing one.

        Updates version, qname, position if changed.
        Preserves name and description.

        Args:
            repo: The repository to use
            node: The node to create/update
            scope_id: Scope ID (for reference, not used for lookup)

        Returns:
            The created or updated node
        """
        # Lookup existing node by qname

        if scope_id:
            existing = repo.get_by_id(scope_id)
        else:
            existing = repo.find_one({"qname": node.qname})

        if existing:
            # Update version
            existing.current_version = node.current_version

            # Update qname if changed
            if existing.qname != node.qname:
                existing.qname = node.qname

            # Update position if it exists and changed
            if hasattr(existing, 'position') and hasattr(node, 'position'):
                if existing.position != node.position:
                    existing.position = node.position

            return repo.update(existing.key, existing)
        else:
            # Create new
            return repo.create(node)

    def ensure_targets_edges_batch(self, edges: list[tuple[str, str]]):
        """
        Batch ensure targets edges exist.
        edges is list of (call_id, callee_id) tuples.
        """
        if not edges:
            return

        t0 = time.time()
        try:
            query = """
            FOR edge IN @edges
                UPSERT { _from: edge.from_id, _to: edge.to_id }
                INSERT { _from: edge.from_id, _to: edge.to_id, version: @version }
                UPDATE { version: @version }
                IN targets_edges
            """
            bind_vars = {
                "edges": [{"from_id": f, "to_id": t} for f, t in edges],
                "version": self.sync_version
            }
            self.repos.targets_edges.db.aql.execute(query, bind_vars=bind_vars)
        except Exception as e:
            logger.error(f"Error ensuring targets edges batch: {e}")
        finally:
            _timings.setdefault('ensure_targets_edge_total', []).append(
                time.time() - t0
            )

    def ensure_contains_edges_batch(self, edges: list[tuple[str, str]]):
        """
        Batch ensure contains edges exist.
        edges is list of (parent_id, child_id) tuples.
        """
        if not edges:
            return

        t0 = time.time()
        try:
            # We use a simplified query that assumes we can just link them.
            # Ideally we'd want the contain_type, but for batch performance
            # we might skip it or derive it if critical.
            # For now, let's use a generic type or try to derive it in AQL if possible,
            # but AQL DOCUMENT() is fast enough.

            query = """
            FOR edge IN @edges
                UPSERT { _from: edge.from_id, _to: edge.to_id }
                INSERT { 
                    _from: edge.from_id, 
                    _to: edge.to_id, 
                    version: @version,
                    contain_type: CONCAT(DOCUMENT(edge.from_id).node_type, "_to_", DOCUMENT(edge.to_id).node_type)
                }
                UPDATE { version: @version }
                IN contains_edges
            """
            bind_vars = {
                "edges": [{"from_id": f, "to_id": t} for f, t in edges],
                "version": self.sync_version
            }
            self.repos.contains_edges.db.aql.execute(
                query, bind_vars=bind_vars)

        except Exception as e:
            logger.error(f"Error ensuring contains edges batch: {e}")
        finally:
            _timings.setdefault('ensure_contains_edge_total', []).append(
                time.time() - t0
            )

    def ensure_targets_edge(self, call_id: str, callee_id: str):
        """
        Ensure a targets edge exists between call node and callee.
        Uses AQL UPSERT to minimize round trips.
        """
        t0 = time.time()
        try:
            query = """
            UPSERT { _from: @from_id, _to: @to_id }
            INSERT { _from: @from_id, _to: @to_id, version: @version }
            UPDATE { version: @version }
            IN targets_edges
            """
            bind_vars = {
                "from_id": call_id,
                "to_id": callee_id,
                "version": self.sync_version
            }
            self.repos.targets_edges.db.aql.execute(query, bind_vars=bind_vars)
        except Exception as e:
            logger.error(
                "Error ensuring targets edge %s -> %s: %s",
                call_id,
                callee_id,
                e,
            )
        finally:
            _timings.setdefault('ensure_targets_edge_total', []).append(
                time.time() - t0
            )

    def ensure_contains_edge(
        self, parent_id: str, child_id: str, version: int
    ):
        """
        Ensure a contains edge exists between parent and child.
        Uses AQL UPSERT to minimize round trips.
        """
        t0 = time.time()
        try:
            # We need to know the contain_type for the INSERT part.
            # However, fetching nodes to determine type adds a round trip.
            # If we can assume a default or fetch only if needed, it's better.
            # For now, let's try to fetch nodes only if we are inserting.
            # Actually, UPSERT in Arango doesn't let us execute arbitrary logic in INSERT block easily
            # without pre-calculating values.
            # But we can do a check-free upsert if we don't strictly need contain_type or can derive it.
            # The original code fetches nodes to get types.

            # Optimization: Try to update first. If it fails (doesn't exist), then fetch nodes and insert.
            # Or better: Just use the UPSERT and calculate type in AQL if possible? No, node types are on nodes.

            # Let's stick to the original logic but optimized:
            # 1. Try to find the edge.
            # 2. If found, update version (1 round trip total if we use AQL UPDATE directly).
            # 3. If not found, fetch nodes and create (2 round trips: fetch nodes, create edge).

            # Even better: Use AQL to do it all?
            # LET edge = FIRST(FOR e IN contains_edges FILTER e._from == @from AND e._to == @to RETURN e)
            # IF edge THEN UPDATE edge WITH {version: @version} IN contains_edges
            # ELSE ... (need node types)

            # Let's use the Python logic but optimize the update case which is common.

            query = """
            UPSERT { _from: @from_id, _to: @to_id }
            INSERT { 
                _from: @from_id, 
                _to: @to_id, 
                version: @version,
                contain_type: CONCAT(DOCUMENT(@from_id).node_type, "_to_", DOCUMENT(@to_id).node_type)
            }
            UPDATE { version: @version }
            IN contains_edges
            """
            # Note: DOCUMENT() function allows us to get the node types inside the query!

            bind_vars = {
                "from_id": parent_id,
                "to_id": child_id,
                "version": version
            }
            self.repos.contains_edges.db.aql.execute(
                query, bind_vars=bind_vars)

        except Exception as e:
            logger.error(
                f"Error ensuring contains edge {parent_id} -> "
                f"{child_id}: {e}"
            )
        finally:
            _timings.setdefault('ensure_contains_edge_total single', []).append(
                time.time() - t0
            )
