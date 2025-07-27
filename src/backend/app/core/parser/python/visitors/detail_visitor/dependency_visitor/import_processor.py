"""
Import statement processor for dependency analysis.

This module handles the processing of import statements (both 'import' and 
'from...import' forms) and registers them in the symbol table for later
resolution during usage detection.
"""

import ast
from typing import List, Union
from ..visitor_context import VisitorContext
from .helpers import get_relative_import_base


class ImportProcessor:
    """
    Processes import statements and registers them in the symbol table.
    
    This class handles both regular imports and from-imports, including
    relative imports and aliased imports.
    """
    
    def __init__(self, context: VisitorContext):
        self.context = context
        self.processed_imports: List[Union[ast.Import, ast.ImportFrom]] = []
    
    def process_import(self, node: ast.Import) -> None:
        """
        Processes 'import module' statements and registers them in the 
        symbol table.
        
        Args:
            node: The ast.Import node to process
        """
        self.processed_imports.append(node)
        
        for alias in node.names:
            import_name = alias.name
            alias_name = alias.asname if alias.asname else alias.name
            
            # Add the import to the symbol table for this file
            self.context.symbol_table.add_import(
                file_id=self.context.file_id,
                alias=alias_name,
                qname=import_name
            )
    
    def process_import_from(self, node: ast.ImportFrom) -> None:
        """
        Processes 'from module import symbol' statements and registers them 
        in the symbol table.
        
        Args:
            node: The ast.ImportFrom node to process
        """
        self.processed_imports.append(node)
        
        # Handle relative imports based on the level (number of dots)
        
        if node.level > 0:
            # This is a relative import (from .module or from ..module)
            parent_module = get_relative_import_base(self.context, node.level)
            if node.module:
                # from .base import something -> parent_module + ".base"
                base_module = (
                    f"{parent_module}.{node.module}" 
                    if parent_module else node.module
                )
            else:
                # from . import something -> just parent_module
                base_module = parent_module
        else:
            # Absolute import
            base_module = node.module
            
        for alias in node.names:
            if alias.name == '*':
                # Handle 'from module import *' - we'll log this as a warning
                # for now and not try to resolve individual symbols
                continue
                
            symbol_name = alias.name
            alias_name = alias.asname if alias.asname else alias.name
            full_qname = (
                f"{base_module}.{symbol_name}" 
                if base_module else symbol_name
            )
            
            # Add the import to the symbol table for this file
            self.context.symbol_table.add_import(
                file_id=self.context.file_id,
                alias=alias_name,
                qname=full_qname
            )
    
    def get_processed_imports(self) -> List[Union[ast.Import, ast.ImportFrom]]:
        """
        Returns the list of processed import nodes.
        
        Returns:
            List of processed import AST nodes
        """
        return self.processed_imports 