from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import CallSiteModel


class CallSiteRepository:
    """Repository for CallSite entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, site: CallSiteModel) -> CallSiteModel:
        """Create and persist a new call site."""
        self.session.add(site)
        self.session.flush()
        return site

    def get_by_id(self, site_id: str) -> Optional[CallSiteModel]:
        """Retrieve call site by ID."""
        return self.session.query(CallSiteModel).filter(CallSiteModel.id == site_id).first()

    def find_by_caller(self, caller_frame_id: str) -> List[CallSiteModel]:
        """
        Get all function calls made from a specific caller frame (forward edges).
        This answers: "What does this frame call?"
        """
        return (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.caller_frame_id == caller_frame_id)
            .all()
        )

    def find_by_callee(self, callee_symbol_id: str) -> List[CallSiteModel]:
        """
        Get all call sites that call a specific function (reverse edges).
        This answers: "Who calls this function?"
        """
        return (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.callee_symbol_id == callee_symbol_id)
            .all()
        )

    def mark_stale(self, source_id: str) -> int:
        """
        Mark all call sites from a source as needing verification.
        Used during incremental analysis when a file changes.
        """
        # Find all frames from this source
        frames_in_source = (
            self.session.query(CallFrameORM)
            .join(ScopeORM, CallFrameORM.execution_scope_id == ScopeORM.id)
            .filter(ScopeORM.source_id == source_id)
            .all()
        )

        frame_ids = [f.id for f in frames_in_source]

        if not frame_ids:
            return 0

        # Mark all call sites from these frames as stale
        count = (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.caller_frame_id.in_(frame_ids))
            .update({"needs_verification": True}, synchronize_session=False)
        )

        return count

    def get_stale_sites(self) -> List[CallSiteModel]:
        """Get all call sites that need verification."""
        return (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.needs_verification == True)
            .all()
        )

    def delete_stale_sites(self) -> int:
        """Delete all stale call sites (cleanup after reanalysis)."""
        count = (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.needs_verification == True)
            .delete()
        )
        return count
