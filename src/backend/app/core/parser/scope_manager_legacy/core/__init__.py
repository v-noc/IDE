from .scope import Scope, ScopeType
from .symbol import Symbol, SymbolType

# Resolve forward references now that both models are imported.
Scope.model_rebuild()
Symbol.model_rebuild()
