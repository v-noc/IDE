from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import ScopeModel, SymbolModel, CallFrameModel, CallSiteModel


class ScopeRepository:
    """Repository for Scope entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, scope: ScopeModel) -> ScopeModel:
        """Create and persist a new scope."""
        self.session.add(scope)
        return scope

    def get_root(self) -> Optional[ScopeModel]:
        """Get the root scope."""
        return self.session.query(ScopeModel).filter(
            ScopeModel.is_root is True
        ).first()

    def get_by_id(self, scope_id: str, include_stale: bool = False) -> Optional[ScopeModel]:
        """Retrieve scope by ID."""
        query = self.session.query(ScopeModel).filter(
            ScopeModel.id == scope_id)
        if not include_stale:
            query = query.filter(ScopeModel.is_stale is False)
        return query.first()

    def get_by_name_in_scope(self, name: str, parent_id: Optional[str], include_stale: bool = False) -> Optional[ScopeModel]:
        """Get a scope by name within a parent scope."""
        query = self.session.query(ScopeModel).filter(ScopeModel.name == name)
        if parent_id:
            query = query.filter(ScopeModel.parent_id == parent_id)
        else:
            query = query.filter(ScopeModel.parent_id.is_(None))

        if not include_stale:
            query = query.filter(ScopeModel.is_stale is False)

        return query.first()

    def get_children(self, parent_id: str, include_stale: bool = False) -> List[ScopeModel]:
        """Get all child scopes."""
        query = self.session.query(ScopeModel).filter(
            ScopeModel.parent_id == parent_id)
        if not include_stale:
            query = query.filter(ScopeModel.is_stale is False)
        return query.all()

    def get_scope_chain(self, scope_id: str) -> List[ScopeModel]:
        """Get the full chain from scope to root (for LEGB traversal)."""
        chain = []
        current_id = scope_id
        while current_id:
            scope = self.get_by_id(current_id)
            if not scope:
                break
            chain.append(scope)
            current_id = scope.parent_id
        return chain

    def get_by_source_unit(self, source_unit_id: str) -> List[ScopeModel]:
        """Get all scopes defined in a source file."""
        return self.session.query(ScopeModel).filter(ScopeModel.source_unit_id == source_unit_id).all()

    def delete_by_source(self, source_unit_id: str) -> int:
        """Delete all scopes in a source file (Resync operation)."""
        count = self.session.query(ScopeModel).filter(
            ScopeModel.source_unit_id == source_unit_id).delete()
        return count

    def get_by_type(self, scope_type: str) -> List[ScopeModel]:
        """Get all scopes of a specific type."""
        return self.session.query(ScopeModel).filter(ScopeModel.scope_type == scope_type).all()

    def mark_tree_stale(self, root_scope_id: str, reason: str) -> int:
        """
        Recursively mark a scope tree as stale.

        Marks:
        1. The root scope and all its descendants
        2. All symbols defined in these scopes
        3. All call frames executed in these scopes
        4. All call sites originating from these frames

        Args:
            root_scope_id: ID of the root scope to mark stale
            reason: Reason string

        Returns:
            Total number of entities marked stale
        """
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()

        # 1. Find all scope IDs in the tree (Iterative BFS)
        scope_ids = {root_scope_id}
        queue = [root_scope_id]

        while queue:
            current_id = queue.pop(0)
            children = self.session.query(ScopeModel.id).filter(
                ScopeModel.parent_id == current_id
            ).all()

            for child in children:
                if child.id not in scope_ids:
                    scope_ids.add(child.id)
                    queue.append(child.id)

        scope_id_list = list(scope_ids)
        if not scope_id_list:
            return 0

        total_marked = 0

        # 2. Bulk update Scopes
        total_marked += self.session.query(ScopeModel).filter(
            ScopeModel.id.in_(scope_id_list)
        ).update({
            "is_stale": True,
            "stale_reason": reason,
            "stale_since": timestamp
        }, synchronize_session=False)

        # 3. Bulk update Symbols
        total_marked += self.session.query(SymbolModel).filter(
            SymbolModel.defining_scope_id.in_(scope_id_list)
        ).update({
            "is_stale": True,
            "stale_reason": reason,
            "stale_since": timestamp
        }, synchronize_session=False)

        # 4. Bulk update CallFrames (execution scopes)
        # First find them to get IDs for CallSites
        frames = self.session.query(CallFrameModel).filter(
            CallFrameModel.execution_scope_id.in_(scope_id_list)
        ).all()

        frame_ids = [f.id for f in frames]

        if frame_ids:
            total_marked += self.session.query(CallFrameModel).filter(
                CallFrameModel.id.in_(frame_ids)
            ).update({
                "is_stale": True,
                "stale_reason": reason,
            }, synchronize_session=False)

            # 5. Bulk update CallSites (outgoing calls from these frames)
            total_marked += self.session.query(CallSiteModel).filter(
                CallSiteModel.caller_frame_id.in_(frame_ids)
            ).update({
                "is_stale": True
            }, synchronize_session=False)

        return total_marked
