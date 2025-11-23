from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import CallFrameModel, CallSiteModel, ScopeModel


class CallSiteRepository:
    """Repository for CallSite entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, site: CallSiteModel) -> CallSiteModel:
        """Create and persist a new call site."""
        self.session.add(site)
        self.session.commit()
        return site

    def get_by_id(self, site_id: str, include_stale: bool = False) -> Optional[CallSiteModel]:
        """Retrieve call site by ID."""
        query = self.session.query(CallSiteModel).filter(
            CallSiteModel.id == site_id)
        if not include_stale:
            query = query.filter(CallSiteModel.is_stale == False)
        return query.first()

    def find_by_caller(self, caller_scope_id: str, include_stale: bool = False) -> List[CallSiteModel]:
        """
        Get all function calls made from a specific caller scope (forward edges).
        This answers: "What does this scope call?"
        """

        query = self.session.query(CallSiteModel).filter(
            CallSiteModel.caller_scope_id == caller_scope_id)
        if not include_stale:
            query = query.filter(CallSiteModel.is_stale == False)
        return query.all()

    def find_by_callee_frame_id(self, callee_frame_id: str, include_stale: bool = False) -> List[CallSiteModel]:
        """
        Get all call sites that call a specific frame (reverse edges).
        This answers: "Who calls this function?"
        """

        query = self.session.query(CallSiteModel).filter(
            CallSiteModel.callee_frame_id == callee_frame_id)

        if not include_stale:
            query = query.filter(CallSiteModel.is_stale == False)
        return query.all()

    def mark_stale(self, source_unit_id: str) -> int:
        """
        Mark all call sites from a source as needing verification.
        Used during incremental analysis when a file changes.
        """
        # Find all frames from this source
        frames_in_source = (
            self.session.query(CallFrameModel)
            .join(ScopeModel, CallFrameModel.execution_scope_id == ScopeModel.id)
            .filter(ScopeModel.source_unit_id == source_unit_id)
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
            .filter(CallSiteModel.is_stale == True)
            .all()
        )

    def delete_stale_sites(self) -> int:
        """Delete all stale call sites (cleanup after reanalysis)."""
        count = (
            self.session.query(CallSiteModel)
            .filter(CallSiteModel.is_stale == True)
            .delete()
        )
        return count
