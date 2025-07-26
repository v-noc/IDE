"""
Context manager for dependency analysis.

This module handles the context management for dependency analysis,
tracking which function or class is currently being analyzed to properly
set the 'from' part of dependency edges.
"""

import ast
from typing import Optional, Callable
from ..visitor_context import VisitorContext
from .helpers import get_file_qname_from_context


class DependencyContextManager:
    """
    Manages context for dependency analysis within functions and classes.
    
    This class tracks the current consumer (function or class) being analyzed
    and provides the context for creating dependency edges.
    """
    
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_consumer_id: Optional[str] = None
        self.class_stack: list = []  # Track class hierarchy for proper qname construction

    def visit_function_def(
        self, 
        node: ast.FunctionDef, 
        visit_body_callback: Callable[[ast.AST], None]
    ) -> None:
        """
        Sets the context for which function is currently being analyzed.
        This determines the 'from' part of UsesImportEdge.
        
        Args:
            node: The ast.FunctionDef node
            visit_body_callback: Callback to visit the function body
        """
        # Get the function's qname by constructing it from the file context
        file_qname = get_file_qname_from_context(self.context)
        
        # Build the function qname considering class hierarchy
        if self.class_stack:
            # If we're inside a class, it's a method
            class_path = ".".join(self.class_stack)
            function_qname = f"{file_qname}.{class_path}.{node.name}"
        else:
            # Top-level function
            function_qname = f"{file_qname}.{node.name}"
        
        # Look up the function's database ID from the symbol table
        function_id = self.context.symbol_table._qname_to_id.get(
            function_qname
        )
        
        if function_id:
            # Store the current consumer for nested visits
            previous_consumer = self.current_consumer_id
            self.current_consumer_id = function_id
            
            # Visit the function body to find import usages
            visit_body_callback(node)
            
            # Restore previous consumer context
            self.current_consumer_id = previous_consumer

    def visit_class_def(
        self, 
        node: ast.ClassDef, 
        visit_body_callback: Callable[[ast.AST], None]
    ) -> None:
        """
        Sets the context for which class is currently being analyzed.
        
        Args:
            node: The ast.ClassDef node
            visit_body_callback: Callback to visit the class body
        """
        # Push the class onto the stack
        self.class_stack.append(node.name)
        
        # Get the class's qname by constructing it from the file context  
        file_qname = get_file_qname_from_context(self.context)
        class_path = ".".join(self.class_stack)
        class_qname = f"{file_qname}.{class_path}"
        
        # Look up the class's database ID from the symbol table
        class_id = self.context.symbol_table._qname_to_id.get(class_qname)
        
        if class_id:
            # Store the current consumer for nested visits
            previous_consumer = self.current_consumer_id
            self.current_consumer_id = class_id
            
            # Visit the class body to find import usages and nested functions
            visit_body_callback(node)
            
            # Restore previous consumer context
            self.current_consumer_id = previous_consumer
        else:
            # Even if class not found, still visit body to process methods
            visit_body_callback(node)
        
        # Pop the class from the stack
        self.class_stack.pop()
    
    def get_current_consumer_id(self) -> Optional[str]:
        """
        Gets the current consumer ID (function or class being analyzed).
        
        Returns:
            The database ID of the current consumer, or None if not set
        """
        return self.current_consumer_id
    
    def has_current_consumer(self) -> bool:
        """
        Checks if there is a current consumer context.
        
        Returns:
            True if there is a current consumer, False otherwise
        """
        return self.current_consumer_id is not None 