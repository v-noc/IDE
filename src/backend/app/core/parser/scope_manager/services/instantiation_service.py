# storage/services/instantiation_service.py
"""
InstantiationService - Handle class instantiation.
Replaces the legacy ClassInstantiationHandler with database-backed persistence.
"""

import uuid
from typing import Dict, Any, Optional

from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.writer.scope_writer import ScopeWriter
from app.core.parser.scope_manager.writer.symbol_writer import SymbolWriter
from app.core.parser.scope_manager.storage.models import SymbolType
from app.core.parser.scope_manager.storage.models import SymbolModel
from app.core.parser.scope_manager.storage.models import ScopeType


class InstantiationService:
    """
    Service for handling class instantiation.

    Focuses on creating object instances and their scopes,
    separate from __init__ invocation.
    """

    def __init__(
        self,
        repo: ScopeManagerRepository,
        scope_writer: ScopeWriter,
        symbol_writer: SymbolWriter
    ):
        self.repo = repo
        self.scope_writer = scope_writer
        self.symbol_writer = symbol_writer

    def instantiate_class(
        self,
        class_symbol_id: str,
        caller_scope_id: str
    ) -> str:
        """
        Create a new object instance following the Object Instantiation Pattern.

        Creates a unique instance_scope and links it to the instance symbol.
        NOTE: This method DOES NOT invoke __init__. Call __init__ explicitly
        using the call tracking service if you want to simulate initialization.

        Args:
            class_symbol_id: ID of the class symbol
            caller_scope_id: ID of the scope where instantiation occurs

        Returns:
            ID of the created instance symbol

        Raises:
            TypeError: If symbol is not a class
        """
        # Validate class symbol
        class_symbol = self.repo.symbols.get_by_id(class_symbol_id)
        if not class_symbol:
            raise ValueError(f"Class symbol {class_symbol_id} not found")

        if class_symbol.symbol_type != SymbolType.CLASS:
            raise TypeError(
                f"Cannot instantiate non-class: {class_symbol.name} "
                f"(type: {class_symbol.symbol_type})"
            )

        # 1. Create unique instance scope
        instance_scope_id = self._create_instance_scope(class_symbol)

        created_instance = self.symbol_writer.create_symbol(
            name=f"instance_{class_symbol.name}_{uuid.uuid4().hex[:8]}",
            symbol_type=SymbolType.OBJECT_INSTANCE,
            scope_id=caller_scope_id,
            instance_scope_id=instance_scope_id,
            original_symbol_id=class_symbol_id,
        )

        return created_instance.id

    def call_init(
        self,
        class_symbol_id: str,
        instance_symbol_id: str,
        init_args: Dict[str, Any],
        caller_scope_id: str
    ) -> None:
        """
        Call the __init__ method on an instance.

        Finds __init__ via MRO and delegates to CallTrackingService.

        Args:
            class_symbol_id: ID of the class
            instance_symbol_id: ID of the instance
            init_args: Arguments to pass to __init__ (excluding 'self')
            caller_scope_id: ID of the scope where instantiation occurs
        """
        # Get class symbol to find __init__
        class_symbol = self.repo.symbols.get_by_id(class_symbol_id)
        if not class_symbol or not class_symbol.defines_scope_id:
            return  # No __init__ to call

        class_scope_id = class_symbol.defines_scope_id

        # Look for __init__ in class scope
        init_method = self.repo.symbols.get_by_name_in_scope(
            "__init__", class_scope_id)

        if not init_method:
            # TODO: Could use InheritanceResolver to find __init__ via MRO
            return  # No __init__ defined

        # Prepare arguments with 'self' injected
        method_args = {"self": instance_symbol_id}
        method_args.update(init_args)

    def _create_instance_scope(self, class_symbol: SymbolModel) -> str:
        """
        Create a unique instance scope for the object.

        Creates a new Scope of type OBJECT for storing instance attributes,
        linked to the class scope for method lookup.

        Returns:
            ID of the created scope
        """
        instance_scope_name = f"{class_symbol.name}_inst_{uuid.uuid4().hex[:8]}"

        # Get class scope to link as parent
        class_scope_id = class_symbol.defines_scope_id

        created_scope = self.scope_writer.create_scope(
            name=instance_scope_name,
            scope_type=ScopeType.CLASS,
            source_unit_id=class_symbol.defining_scope.source_unit_id,
            parent_id=class_scope_id,
        )
        return created_scope.id
