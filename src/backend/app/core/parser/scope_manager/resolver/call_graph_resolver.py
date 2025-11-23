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
        root_scope_id: str,
        max_depth: int = 5
    ) -> dict:
        """
        Build a tree representation of calls from a root frame.

        Args:
            root_scope_id: Starting scope
            max_depth: How deep to traverse

        Returns:
            Nested dict representing the call tree

        Example:
            {
                'frame_id': 'frame_123',
                'callee_symbol': 'SymbolModel',
                'children': [
                    {'frame_id': 'frame_124', 'callee_symbol': 'SymbolModel', 'children': [...]},
                    {'frame_id': 'frame_125', 'callee_symbol': 'SymbolModel', 'children': []},
                ]
            }
        """
        def _build_tree(execution_scope_id: str, depth: int) -> Optional[dict]:
            if depth >= max_depth:
                return None

            call_sites = self.repo.call_sites.find_by_caller(
                execution_scope_id)

            tree = []

            for site in call_sites:
                # Find the frame for this call site
                # (in practice, we'd need to track which frame was created for each call site)
                # For now, find frames with matching callee
                child_frames = site.callee_frame
                if child_frames:
                    tree.append({
                        'frame_id': child_frames.id,
                        'callee_symbol': child_frames.callee_symbol,
                        'children': _build_tree(child_frames.execution_scope_id, depth + 1)
                    })

            return tree

        return _build_tree(root_scope_id, 0)
