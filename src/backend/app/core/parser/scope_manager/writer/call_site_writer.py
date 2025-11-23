# storage/writers/call_site_writer.py
"""
CallSiteWriter - Handles creation of call edges in the call graph.
Part of the Writer Layer in the call graph architecture.
"""

import uuid
from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import CallSiteModel


class CallSiteWriter:
    """
    Writer for CallSite entities.
    Call sites represent the call graph structure and need careful validation
    during incremental updates.
    """

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def create_call_site(
        self,
        caller_scope_id: str,
        callee_frame_id: str
    ) -> str:
        """
        Create a call edge in the call graph.

        Args:
            caller_scope_id: ID of the scope making the call
            callee_frame_id: ID of the frame being called

        Returns:
            The ID of the created call site

        Raises:
            ValueError: If validation fails
        """
        # Generate unique ID
        site_id = str(uuid.uuid4())

        # Build ORM entity
        call_site = CallSiteModel(
            id=site_id,
            caller_scope_id=caller_scope_id,
            callee_frame_id=callee_frame_id,

        )

        # Validate before persisting
        self._validate_call_site(call_site)

        # Persist to database
        self.repo.call_sites.create(call_site)

        return site_id

    def mark_stale(self, source_id: str) -> int:
        """
        Mark all call sites from a source file as stale.
        Used during incremental analysis when a file changes.

        Args:
            source_id: ID of the source file that changed

        Returns:
            Number of call sites marked as stale
        """
        return self.repo.call_sites.mark_stale(source_id)

    def cleanup_stale_sites(self) -> int:
        """
        Delete all stale call sites (cleanup after reanalysis).

        Returns:
            Number of call sites deleted
        """
        return self.repo.call_sites.delete_stale_sites()

    def _validate_call_site(self, call_site: CallSiteModel) -> None:
        """
        Validation before persistence.

        Raises:
            ValueError: If validation fails
        """
        # Verify caller scope exists
        caller_scope = self.repo.scopes.get_by_id(
            call_site.caller_scope_id)

        if not caller_scope:
            raise ValueError(
                f"Caller scope {call_site.caller_scope_id} not found"
            )

        # Verify callee symbol exists
        callee_frame = self.repo.call_frames.get_by_id(
            call_site.callee_frame_id)
        if not callee_frame:
            raise ValueError(
                f"Callee frame {call_site.callee_frame_id} not found"
            )
