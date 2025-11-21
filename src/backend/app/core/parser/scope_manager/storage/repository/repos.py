from sqlalchemy.orm import Session
from .scope_repo import ScopeRepository
from .symbol_repo import SymbolRepository
from .source_unit_repo import SourceUnitRepository
from .dependency_edge_repo import DependencyEdgeRepository
from .call_frame_repo import CallFrameRepository
from .call_site_repo import CallSiteRepository


class ScopeManagerRepository:
    """
    Unified repository providing all data access patterns.
    Acts as a facade to all specialized repositories.
    """

    def __init__(self, session: Session):
        self.session = session
        self.scopes = ScopeRepository(session)
        self.symbols = SymbolRepository(session)
        self.sources = SourceUnitRepository(session)
        self.dependencies = DependencyEdgeRepository(session)
        self.call_frames = CallFrameRepository(session)
        self.call_sites = CallSiteRepository(session)

    def commit(self):
        """Commit the current transaction."""
        self.session.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.session.rollback()
