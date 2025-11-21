# storage/writers/symbol_writer.py
"""
Symbol Writer - Handle creation and management of symbols.
"""

import uuid
from typing import Optional, Dict, Any
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SymbolType, SymbolModel


class SymbolWriter:
    """Write operations for symbols."""

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def create_symbol(
        self,
        name: str,
        symbol_type: SymbolType,
        scope_id: str,
        defines_scope_id: Optional[str] = None,
        assigned_to_id: Optional[str] = None,
        instance_scope_id: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> SymbolModel:
        """
        Create a new symbol.

        Args:
            name: Symbol name
            symbol_type: Type of symbol
            scope_id: Scope where defined
            defines_scope_id: Scope where defined
            assigned_to_id: Optional - what it's assigned to
            instance_scope_id: Optional - instance scope
            attrs: Optional - metadata attributes

        Returns:
            The created symbol
        """
        symbol = SymbolModel(
            id=str(uuid.uuid4()),
            name=name,
            symbol_type=symbol_type.value,
            defining_scope_id=scope_id,
            defines_scope_id=defines_scope_id,
            assigned_to_id=assigned_to_id,
            instance_scope_id=instance_scope_id,
            attrs=attrs or {},
        )
        return self.repo.symbols.create(symbol)

    def update_symbol_attrs(self, symbol_id: str, attrs: Dict[str, Any]) -> bool:
        """
        Update symbol attributes/metadata.

        Args:
            symbol_id: The symbol ID
            attrs: Attributes to set

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            symbol.attrs = attrs
            return True
        return False

    def add_to_symbol_attrs(
        self, symbol_id: str, key: str, value: Any
    ) -> bool:
        """
        Add a key-value pair to symbol attributes.

        Args:
            symbol_id: The symbol ID
            key: Attribute key
            value: Attribute value

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol:
            if symbol.attrs is None:
                symbol.attrs = {}
            symbol.attrs[key] = value
            return True
        return False

    def remove_from_symbol_attrs(self, symbol_id: str, key: str) -> bool:
        """
        Remove a key from symbol attributes.

        Args:
            symbol_id: The symbol ID
            key: Attribute key to remove

        Returns:
            True if successful, False otherwise
        """
        symbol = self.repo.symbols.get_by_id(symbol_id)
        if symbol and symbol.attrs and key in symbol.attrs:
            del symbol.attrs[key]
            return True
        return False
