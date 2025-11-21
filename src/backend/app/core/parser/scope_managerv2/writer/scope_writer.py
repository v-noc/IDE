# storage/writers/scope_writer.py
"""
Scope Writer - Handle creation and management of scopes.
"""

import uuid
from typing import Optional
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import ScopeType, ScopeModel


class ScopeWriter:
    """Write operations for scopes."""

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def create_scope(
        self,
        name: str,
        scope_type: ScopeType,
        source_unit_id: str,
        is_root: bool = False,
        parent_id: Optional[str] = None,
    ) -> ScopeModel:
        """
        Create a new scope.

        Args:
            name: Scope name
            scope_type: Type of scope
            source_unit_id: Source file ID
            is_root: Whether the scope is the root scope
            parent_id: Parent scope ID (optional)

        Returns:
            The created scope
        """
        scope = ScopeModel(
            id=str(uuid.uuid4()),
            name=name,
            scope_type=scope_type.value,
            source_unit_id=source_unit_id,
            is_root=is_root,
            parent_id=parent_id,
        )
        return self.repo.scopes.create(scope)

    def set_scope_base_classes(self, scope_id: str, base_class_ids: list) -> bool:
        """
        Set the base classes for a class scope.

        Args:
            scope_id: The class scope ID
            base_class_ids: List of base class scope IDs

        Returns:
            True if successful, False otherwise
        """
        scope = self.repo.scopes.get_by_id(scope_id)
        if scope:
            scope.base_classes_ids = [
                ScopeModel(id=id) for id in base_class_ids]
            return True
        return False
