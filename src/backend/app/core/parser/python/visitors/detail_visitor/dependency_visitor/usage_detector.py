"""
Usage detector for dependency analysis.

This module detects usage of imported symbols within the code, including
both simple name references and complex attribute access chains.
"""

import ast
from ..visitor_context import VisitorContext
from app.models.node import NodePosition
from .helpers import reconstruct_attribute_chain, create_usage_edge


class UsageDetector:
    """
    Detects usage of imported symbols in the code.
    
    This class handles both simple name references (like 'Request') and
    complex attribute access (like 'np.array' or 'requests.get().json()').
    """
    
    def __init__(
        self, 
        context: VisitorContext, 
        get_current_consumer_id_func,
        get_processed_imports_func
    ):
        self.context = context
        self.get_current_consumer_id = get_current_consumer_id_func
        self.get_processed_imports = get_processed_imports_func
    
    def detect_name_usage(self, node: ast.Name) -> None:
        """
        Handles usage of simple imported names, like 'Request' in 
        'from fastapi import Request'.
        
        Args:
            node: The ast.Name node representing the name usage
        """
        current_consumer_id = self.get_current_consumer_id()
        
        if not current_consumer_id or not isinstance(node.ctx, ast.Load):
            return
            
        # Check if this name is an imported symbol
        resolved_qname = self.context.symbol_table.resolve_import_qname(
            file_id=self.context.file_id,
            name=node.id
        )
        
        if resolved_qname:
            create_usage_edge(
                context=self.context,
                current_consumer_id=current_consumer_id,
                processed_imports=self.get_processed_imports(),
                target_qname=resolved_qname,
                target_symbol=node.id,
                alias=node.id,
                usage_position=NodePosition(
                    line_no=node.lineno,
                    col_offset=node.col_offset,
                    end_line_no=getattr(node, 'end_lineno', node.lineno),
                    end_col_offset=getattr(
                        node, 'end_col_offset', node.col_offset
                    )
                )
            )
    
    def detect_attribute_usage(
        self, 
        node: ast.Attribute,
        visit_callback
    ) -> None:
        """
        Handles usage of aliased imports, like 'np.array' where 'np' is an 
        alias for 'numpy'.
        
        Args:
            node: The ast.Attribute node representing the attribute access
            visit_callback: Callback to continue visiting child nodes
        """
        current_consumer_id = self.get_current_consumer_id()
        
        if not current_consumer_id or not isinstance(node.ctx, ast.Load):
            return
            
        # Reconstruct the full attribute access chain
        name_chain = reconstruct_attribute_chain(node)
        
        if not name_chain:
            return
            
        # Check if the base name is an imported symbol
        base_name = name_chain[0]
        resolved_qname = self.context.symbol_table.resolve_import_qname(
            file_id=self.context.file_id,
            name=base_name
        )
        
        if resolved_qname:
            # For attribute access, we need to distinguish between:
            # 1. Module-level access (numpy.array) - separate symbol
            # 2. Class-level access (UserType.ADMIN) - field/method
            
            if len(name_chain) > 1:
                # First try the full qname (for module-level access)
                full_target_qname = (
                    f"{resolved_qname}.{'.'.join(name_chain[1:])}"
                )
                
                # Check if this full qname exists in the symbol table
                if self.context.symbol_table.get_symbol_id(full_target_qname):
                    # It exists - this is module-level attribute access
                    target_qname = full_target_qname
                    target_symbol = node.attr
                else:
                    # It doesn't exist - this is likely class attribute access
                    # Create edge to the base class/object instead
                    target_qname = resolved_qname
                    target_symbol = base_name
            else:
                target_qname = resolved_qname
                target_symbol = base_name
                
            create_usage_edge(
                context=self.context,
                current_consumer_id=current_consumer_id,
                processed_imports=self.get_processed_imports(),
                target_qname=target_qname,
                target_symbol=target_symbol,
                alias=base_name,
                usage_position=NodePosition(
                    line_no=node.lineno,
                    col_offset=node.col_offset,
                    end_line_no=getattr(node, 'end_lineno', node.lineno),
                    end_col_offset=getattr(
                        node, 'end_col_offset', node.col_offset
                    )
                )
            )
        
        # Continue visiting the attribute value
        visit_callback(node) 