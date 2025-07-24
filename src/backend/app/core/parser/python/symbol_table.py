# src/backend/app/core/parser/python/symbol_table.py
from typing import Dict, List, Optional

class SymbolTable:
    """
    The central component for resolving names, types, and dependencies.
    It acts as a stateful, in-memory cache and resolution engine that sits
    in front of the ArangoDB database.
    """
    def __init__(self):
        self._qname_to_id: Dict[str, str] = {}
        self._file_id_to_imports: Dict[str, Dict[str, str]] = {}
        self._scope_stack: List[str] = []

    def add_symbol(self, qname: str, db_id: str) -> None:
        """Caches a symbol's qname and its database ID."""
        self._qname_to_id[qname] = db_id

    def add_import(self, file_id: str, alias: str, qname: str) -> None:
        # To be implemented in Phase 2
        pass

    def push_scope(self, scope_id: str) -> None:
        # To be implemented in Phase 4
        pass

    def pop_scope(self) -> Optional[str]:
        # To be implemented in Phase 4
        pass

    def resolve_call_target_to_id(self, call_node, scope_id: str) -> Optional[str]:
        # To be implemented in Phase 4
        pass
