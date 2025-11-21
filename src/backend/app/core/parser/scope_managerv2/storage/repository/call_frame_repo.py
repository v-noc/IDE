from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import CallFrameModel, CallSiteModel


class CallFrameRepository:
    """Repository for CallFrame entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, frame: CallFrameModel) -> CallFrameModel:
        """Create and persist a new call frame."""
        self.session.add(frame)
        self.session.flush()
        return frame

    def get_by_id(self, frame_id: str, include_stale: bool = True) -> Optional[CallFrameModel]:
        """Retrieve call frame by ID."""
        query = self.session.query(CallFrameModel).filter(
            CallFrameModel.id == frame_id)
        if not include_stale:
            query = query.filter(CallFrameModel.is_stale == False)
        return query.first()

    def get_by_execution_scope(self, scope_id: str, include_stale: bool = True) -> Optional[CallFrameModel]:
        """Find the call frame for a specific execution scope."""
        query = self.session.query(CallFrameModel).filter(
            CallFrameModel.execution_scope_id == scope_id)
        if not include_stale:
            query = query.filter(CallFrameModel.is_stale == False)
        return query.first()

    def get_by_callee(self, callee_id: str, include_stale: bool = True) -> List[CallFrameModel]:
        """Get all call frames for a callee symbol (all invocations of a function)."""
        query = self.session.query(CallFrameModel).filter(
            CallFrameModel.callee_symbol_id == callee_id)
        if not include_stale:
            query = query.filter(CallFrameModel.is_stale == False)
        return query.all()

    def get_active_frames(self, limit: int = 100) -> List[CallFrameModel]:
        """
        Get recent call frames (for debugging and visualization).
        Returns frames ordered by ID (most recent first).
        """
        return (
            self.session.query(CallFrameModel)
            .order_by(CallFrameModel.id.desc())
            .limit(limit)
            .all()
        )

    def count_by_depth(self, depth: int) -> int:
        """Count frames at a specific call depth (for recursion detection)."""
        return (
            self.session.query(CallFrameModel)
            .filter(CallFrameModel.call_depth == depth)
            .count()
        )

    def get_stack_depth(self, frame_id: str) -> int:
        """
        Calculate the stack depth for a frame by counting parent frames.
        """
        depth = 0
        current_id = frame_id
        while current_id:
            frame = self.get_by_id(current_id)
            if not frame:
                break
            depth += 1
            current_id = frame.parent_frame_id
        return depth
