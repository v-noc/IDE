# storage/services/call_tracking_service.py
"""
CallTrackingService - Main orchestration layer for call graph tracking.
Replaces the legacy CallGraphTracker with database-backed persistence.
"""

import uuid
from typing import Dict, Any, Optional

from app.core.parser.scope_manager.storage.repository.repos import ScopeManagerRepository
from app.core.parser.scope_manager.storage.models import ScopeModel, SymbolModel, SymbolType
from app.core.parser.scope_manager.storage.models import CallFrameModel
from app.core.parser.scope_manager.writer.call_frame_writer import CallFrameWriter
from app.core.parser.scope_manager.writer.call_site_writer import CallSiteWriter
from app.core.parser.scope_manager.storage.models import ScopeType


class CallTrackingService:
    """
    Service for tracking function calls and building the call graph.

    Coordinates multiple writers and enforces business rules like
    recursion limits and closure capture.
    """

    def __init__(
        self,
        repo: ScopeManagerRepository,
        frame_writer: CallFrameWriter,
        site_writer: CallSiteWriter,
        max_recursion_depth: int = 100
    ):
        self.repo = repo
        self.frame_writer = frame_writer
        self.site_writer = site_writer
        self.max_recursion_depth = max_recursion_depth

    def start_call(
        self,
        callee_symbol_id: str,
        args: Dict[str, Any],
        caller_scope_id: Optional[str] = None
    ) -> str:
        """
        Start a new function call.

        This is the core entry point that orchestrates:
        1. Recursion checking
        2. Execution scope creation
        3. Call frame creation
        4. Argument population
        5. Call edge creation

        Args:
            callee_symbol_id: ID of the function/method being called
            args: Dictionary of argument name -> value (symbol ID or literal)
            caller_scope_id: ID of the calling scope (None for root calls)

        Returns:
            ID of the created call frame

        Raises:
            RecursionError: If maximum recursion depth is exceeded
            ValueError: If callee symbol is invalid
        """
        # 1. Business rule: Check recursion depth
        current_depth = self._get_current_depth(caller_scope_id)
        if current_depth >= self.max_recursion_depth:
            raise RecursionError(
                f"Maximum call depth exceeded: {self.max_recursion_depth}"
            )

        #  2. Create unique execution scope for this call
        callee_symbol = self.repo.symbols.get_by_id(callee_symbol_id)

        if not callee_symbol:
            raise ValueError(f"Callee symbol {callee_symbol_id} not found")

        execution_scope_id = self._create_execution_scope(callee_symbol)

        # 3. Create call frame
        frame_id = self.frame_writer.create_frame(
            callee_symbol_id=callee_symbol_id,
            execution_scope_id=execution_scope_id,

            call_depth=current_depth + 1
        )

        # 4. Populate execution scope with arguments
        self._populate_arguments(frame_id, execution_scope_id, args)

        # 5. Create call edge (if not root call)

        self.site_writer.create_call_site(
            caller_scope_id, frame_id)

        return frame_id

    def end_call(
        self,
        frame_id: str,
        return_symbol_id: Optional[str] = None
    ) -> Optional[SymbolModel]:
        """
        End a function call.

        Handles the CRITICAL closure capture logic:
        - If returning a function, creates a closure symbol with captured_scope_id
        - Updates the frame with the return value

        Args:
            frame_id: ID of the frame to complete
            return_symbol_id: ID of the symbol being returned (None if no return)

        Returns:
            ID of the (possibly transformed) return symbol

        Raises:
            RuntimeError: If frame not found
        """
        frame = self.repo.call_frames.get_by_id(frame_id)
        if not frame:
            raise RuntimeError(f"Frame {frame_id} not found")

        # CRITICAL CLOSURE LOGIC:
        # If returning a function, stamp it with the captured frame
        processed_return = self._process_return_value(
            return_symbol_id, frame)

        processed_return_id = None

        if processed_return:
            processed_return_id = processed_return.id
        # Update frame with return value
        self.frame_writer.complete_frame(frame_id, processed_return_id)

        return processed_return

    def get_current_depth(self) -> int:
        """Get current call stack depth."""
        # This would require tracking active frames
        # For now, return 0 as a placeholder
        # TODO: Implement active frame tracking
        return 0

    def _get_current_depth(self, caller_scope_id: Optional[str]) -> int:
        """
        Calculate depth by walking parent chain.
        """
        if not caller_scope_id:
            return 0

        return self.repo.call_frames.get_stack_depth(caller_scope_id)

    def _create_execution_scope(self, callee_symbol: SymbolModel) -> str:
        """
        Create a unique execution scope for a function call.

        Returns:
            ID of the created scope
        """
        scope_name = f'exec_{callee_symbol.name}_{uuid.uuid4().hex[:8]}'

        scope = ScopeModel(
            id=str(uuid.uuid4()),
            name=scope_name,
            scope_type=ScopeType.FUNCTION,  # or EXECUTION if you have it
            parent_id=callee_symbol.defining_scope_id,
            # Runtime scopes don't belong to a source
            source_unit_id=callee_symbol.defining_scope.source_unit_id
        )

        created_scope = self.repo.scopes.create(scope)
        return created_scope.id

    def _populate_arguments(
        self,
        frame_id: str,
        execution_scope_id: str,
        arguments: Dict[str, Any]
    ) -> None:
        """
        Populate the execution scope with function arguments.

        Always creates parameter symbols in the execution scope.
        If an argument value is a symbol ID or SymbolModel, links via assigned_to_id.
        """
        for param_name, arg_value in arguments.items():
            # Create a parameter symbol local to the execution scope
            param_symbol = SymbolModel(
                id=str(uuid.uuid4()),
                name=param_name,
                symbol_type=SymbolType.PARAMETER,
                defining_scope_id=execution_scope_id,
            )

            # Handle SymbolModel objects directly (for convenience)
            if isinstance(arg_value, SymbolModel):
                param_symbol.assigned_to_id = arg_value.id
            # If the argument is a symbol ID (string), link it
            elif isinstance(arg_value, str):
                # Check if it's a valid symbol ID
                target_symbol = self.repo.symbols.get_by_id(arg_value)
                if target_symbol:
                    param_symbol.assigned_to_id = arg_value
                else:
                    # It's a string literal, store as metadata
                    param_symbol.attrs = {"literal_value": arg_value}
            else:
                # Literal value (int, bool, etc.), store as metadata
                param_symbol.attrs = {"literal_value": arg_value}

            self.repo.symbols.create(param_symbol)

    def _process_return_value(
        self,
        return_symbol_id: Optional[str],
        frame: CallFrameModel
    ) -> Optional[SymbolModel]:
        """
        Process return value and handle closure capture.

        This is WHERE THE MAGIC HAPPENS for higher-order functions.
        If returning a function, creates a closure symbol that captures the frame.

        Returns:
            ID of the (possibly new) return symbol
        """
        if not return_symbol_id:
            return None

        return_symbol = self.repo.symbols.get_by_id(return_symbol_id)
        if not return_symbol:
            return None

        # If returning a function, it becomes a closure
        if return_symbol.symbol_type == SymbolType.FUNCTION:
            # Create a new closure symbol
            closure_symbol = SymbolModel(
                id=str(uuid.uuid4()),
                name=return_symbol.name,
                symbol_type=SymbolType.CAPTURED_CLOSURE,
                defining_scope_id=frame.execution_scope_id,
                captured_frame_id=frame.id,  # CRITICAL: Link to captured frame
                original_symbol_id=return_symbol.id,  # Link back to original function
                attrs=return_symbol.attrs.copy() if return_symbol.attrs else {}
            )

            created_closure = self.repo.symbols.create(closure_symbol)
            return created_closure

        # Otherwise, return as-is
        return return_symbol
