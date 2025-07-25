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
            # Construct the full target qname
            if len(name_chain) > 1:
                full_target_qname = (
                    f"{resolved_qname}.{'.'.join(name_chain[1:])}"
                )
            else:
                full_target_qname = resolved_qname
                
            create_usage_edge(
                context=self.context,
                current_consumer_id=current_consumer_id,
                processed_imports=self.get_processed_imports(),
                target_qname=full_target_qname,
                target_symbol=node.attr,
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