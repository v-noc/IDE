# storage/resolvers/call_graph_resolver.py
"""
CallGraphResolver - Query the call graph structure.
Part of the Resolver Layer in the call graph architecture.
"""

from typing import List, Optional, Set

from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import CallSiteModel, CallFrameModel


class CallGraphResolver:
    """
    Resolver for querying the call graph structure.
    Provides read-only queries separated from write operations
    for better testability and caching.
    """

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def get_root_call_from_scope(self, scope_id: str) -> List[CallFrameModel]:
        """
        Get the root call from a scope.
        """
        return self.repo.call_sites.find_by_caller(scope_id)

    def get_callees(self, caller_frame_id: str) -> List[CallSiteModel]:
        """
        Get all functions called from a specific frame (forward edges).

        Args:
            caller_frame_id: ID of the caller frame

        Returns:
            List of call sites representing outgoing calls

        Example:
            If frame_123 calls [func_a, func_b], returns:
            [CallSite(callee=func_a), CallSite(callee=func_b)]
        """
        return self.repo.call_sites.find_by_caller(caller_frame_id)

    def get_callers(self, callee_symbol_id: str) -> List[CallSiteModel]:
        """
        Get all call sites that call a specific function (reverse edges).

        Args:
            callee_symbol_id: ID of the function being called

        Returns:
            List of call sites representing incoming calls

        Example:
            If [frame_1, frame_2] call func_x, returns:
            [CallSite(caller=frame_1), CallSite(caller=frame_2)]
        """
        return self.repo.call_sites.find_by_callee(callee_symbol_id)

    def get_call_chain(
        self,
        from_symbol_id: str,
        to_symbol_id: str,
        max_depth: int = 10
    ) -> Optional[List[CallSiteModel]]:
        """
        Find a call path from one function to another.

        Args:
            from_symbol_id: Starting function
            to_symbol_id: Target function
            max_depth: Maximum path length to search

        Returns:
            List of call sites forming a path, or None if no path exists

        Example:
            Path: main -> process -> parse
            Returns: [CallSite(main->process), CallSite(process->parse)]
        """
        # Use BFS to find shortest path
        visited: Set[str] = set()
        queue: List[tuple[List[CallSiteModel], str]] = [([], from_symbol_id)]

        while queue:
            path, current_symbol = queue.pop(0)

            if len(path) >= max_depth:
                continue

            if current_symbol == to_symbol_id:
                return path

            if current_symbol in visited:
                continue

            visited.add(current_symbol)

            # Get all frames that called this symbol
            frames = self.repo.call_frames.get_by_callee(current_symbol)

            for frame in frames:
                # Get calls made from this frame
                call_sites = self.repo.call_sites.find_by_caller(frame.id)

                for site in call_sites:
                    if site.callee_symbol_id not in visited:
                        new_path = path + [site]
                        queue.append((new_path, site.callee_symbol_id))

        return None  # No path found

    def detect_recursion(
        self,
        symbol_id: str,
        max_depth: int = 100
    ) -> bool:
        """
        Check if a function is recursive by looking for cycles.

        Args:
            symbol_id: ID of the function to check
            max_depth: Maximum depth to search

        Returns:
            True if function calls itself (directly or indirectly)
        """
        # Check if any call site creates a cycle
        call_chain = self.get_call_chain(symbol_id, symbol_id, max_depth)
        return call_chain is not None and len(call_chain) > 0

    def get_call_tree(
        self,
        root_frame_id: str,
        max_depth: int = 5
    ) -> dict:
        """
        Build a tree representation of calls from a root frame.

        Args:
            root_frame_id: Starting frame
            max_depth: How deep to traverse

        Returns:
            Nested dict representing the call tree

        Example:
            {
                'frame_id': 'frame_123',
                'callee': 'main',
                'children': [
                    {'frame_id': 'frame_124', 'callee': 'process', 'children': [...]},
                    {'frame_id': 'frame_125', 'callee': 'cleanup', 'children': []},
                ]
            }
        """
        def _build_tree(execution_scope_id: str, depth: int) -> Optional[dict]:
            if depth >= max_depth:
                return None

            frame = self.repo.call_sites.find_by_caller(execution_scope_id)
            if not frame:
                return None

            callee_symbol = self.repo.symbols.get_by_id(frame.callee_symbol_id)

            tree = {
                'frame_id': frame_id,
                'callee': callee_symbol.name if callee_symbol else 'unknown',
                'callee_id': frame.callee_symbol_id,
                'children': []
            }

            # Get all calls made from this frame
            call_sites = self.repo.call_sites.find_by_caller(frame_id)

            for site in call_sites:
                # Find the frame for this call site
                # (in practice, we'd need to track which frame was created for each call site)
                # For now, find frames with matching callee
                child_frames = self.repo.call_frames.get_by_callee(
                    site.callee_symbol_id)

                for child_frame in child_frames:
                    if child_frame.execution_scope_id == frame_id:
                        child_tree = _build_tree(child_frame.id, depth + 1)
                        if child_tree:
                            tree['children'].append(child_tree)

            return tree

        return _build_tree(root_frame_id, 0)

    def get_most_called_functions(self, limit: int = 10) -> List[tuple[str, int]]:
        """
        Get the most frequently called functions.

        Args:
            limit: Number of results to return

        Returns:
            List of (symbol_id, call_count) tuples, sorted by count
        """
        from sqlalchemy import func

        results = (
            self.repo.session.query(
                CallSiteModel.callee_symbol_id,
                func.count(CallSiteModel.id).label('call_count')
            )
            .group_by(CallSiteModel.callee_symbol_id)
            .order_by(func.count(CallSiteModel.id).desc())
            .limit(limit)
            .all()
        )

        return [(symbol_id, count) for symbol_id, count in results]
