from .scope_repo import ScopeRepository
from .symbol_repo import SymbolRepository
from .call_frame_repo import CallFrameRepository
from .call_site_repo import CallSiteRepository
from .source_unit_repo import SourceUnitRepository
from .dependency_edge_repo import DependencyEdgeRepository

__all__ = [
    "ScopeRepository",
    "SymbolRepository",
    "CallFrameRepository",
    "CallSiteRepository",
    "SourceUnitRepository",
    "DependencyEdgeRepository"
]
