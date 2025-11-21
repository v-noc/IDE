from ..storage.repository.repos import ScopeManagerRepository
from .scope_writer import ScopeWriter
from .symbol_writer import SymbolWriter
from .source_writer import SourceWriter
from .assignment_writer import AssignmentWriter
from .call_frame_writer import CallFrameWriter
from .call_site_writer import CallSiteWriter
from .scope_writer import ScopeWriter
from .symbol_writer import SymbolWriter


class Writer:
    """
    Writer for the scope manager.
    """

    def __init__(self, repo: ScopeManagerRepository):
        self.scope_writer = ScopeWriter(repo)
        self.symbol_writer = SymbolWriter(repo)
        self.source_writer = SourceWriter(repo)
        self.assignment_writer = AssignmentWriter(repo)
        self.call_frame_writer = CallFrameWriter(repo)
        self.call_site_writer = CallSiteWriter(repo)
