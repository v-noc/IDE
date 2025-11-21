from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import SymbolModel


class SymbolRepository:
    """Repository for Symbol entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, symbol: SymbolModel) -> SymbolModel:
        """Create and persist a new symbol."""
        self.session.add(symbol)
        self.session.flush()
        return symbol

    def get_by_id(self, symbol_id: str, include_stale: bool = True) -> Optional[SymbolModel]:
        """Retrieve symbol by ID."""
        query = self.session.query(SymbolModel).filter(
            SymbolModel.id == symbol_id)
        if not include_stale:
            query = query.filter(SymbolModel.is_stale == False)
        return query.first()

    def get_in_scope(self, scope_id: str, include_stale: bool = True) -> List[SymbolModel]:
        """Get all symbols defined in a scope."""
        query = self.session.query(SymbolModel).filter(
            SymbolModel.defining_scope_id == scope_id)
        if not include_stale:
            query = query.filter(SymbolModel.is_stale == False)
        return query.all()

    def get_by_name_in_scope(self, name: str, scope_id: str, include_stale: bool = True) -> Optional[SymbolModel]:
        """Get a symbol by name within a specific scope."""
        query = self.session.query(SymbolModel).filter(
            and_(SymbolModel.name == name,
                 SymbolModel.defining_scope_id == scope_id)
        )
        if not include_stale:
            query = query.filter(SymbolModel.is_stale == False)
        return query.first()

    def get_by_type(self, symbol_type: str) -> List[SymbolModel]:
        """Get all symbols of a specific type."""
        return (
            self.session.query(SymbolModel)
            .filter(SymbolModel.symbol_type == symbol_type)
            .all()
        )

    def get_by_assigned_to(self, symbol_id: str) -> List[SymbolModel]:
        """Get all symbols assigned to this symbol (aliases)."""
        return (
            self.session.query(SymbolModel)
            .filter(SymbolModel.assigned_to_id == symbol_id)
            .all()
        )
