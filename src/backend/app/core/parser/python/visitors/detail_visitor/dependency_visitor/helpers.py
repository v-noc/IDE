"""
Helper utilities for dependency analysis.

This module contains utility functions used by the dependency visitor
components for common operations like qname resolution, attribute chain
reconstruction, and edge creation.
"""

import ast
from typing import List, Optional
from ..visitor_context import VisitorContext
from app.models.edges import UsesImportEdge
from app.models.node import NodePosition


def get_file_qname_from_context(context: VisitorContext) -> str:
    """
    Extracts the file's qname from the current context.
    
    Args:
        context: The visitor context containing symbol table and file info
        
    Returns:
        The qualified name of the current file
    """
    # Find the file qname by looking through the symbol table
    for qname, node_id in context.symbol_table._qname_to_id.items():
        if node_id == context.file_id:
            return qname
    
    # Fallback: construct from file path if not found
    return "unknown_file"


def get_relative_import_base(context: VisitorContext, level: int) -> str:
    """
    Calculates the base module for relative imports based on the level.
    
    Args:
        context: The visitor context
        level: The relative import level (number of dots)
        
    Returns:
        The base module name for the relative import
    """
    file_qname = get_file_qname_from_context(context)
    parts = file_qname.split('.')
    
    if level >= len(parts):
        return ""  # Invalid relative import
        
    return '.'.join(parts[:-level]) if level > 0 else file_qname


def reconstruct_attribute_chain(node: ast.Attribute) -> List[str]:
    """
    Reconstructs the full chain of attribute access.
    
    For example, 'a.b.c' becomes ['a', 'b', 'c'].
    
    Args:
        node: The ast.Attribute node to analyze
        
    Returns:
        List of names in the attribute chain, or empty list if complex
    """
    chain = [node.attr]
    current = node.value
    
    while isinstance(current, ast.Attribute):
        chain.insert(0, current.attr)
        current = current.value
        
    if isinstance(current, ast.Name):
        chain.insert(0, current.id)
        return chain
        
    return []  # Complex expression, can't resolve


def create_usage_edge(
    context: VisitorContext,
    current_consumer_id: str,
    processed_imports: List,
    target_qname: str, 
    target_symbol: str, 
    alias: str, 
    usage_position: NodePosition
) -> None:
    """
    Creates a UsesImportEdge and adds it to the results.
    
    Args:
        context: The visitor context
        current_consumer_id: The ID of the current consumer
        processed_imports: List of processed import nodes
        target_qname: The fully qualified name of the target
        target_symbol: The specific symbol being used
        alias: The alias used for the import
        usage_position: Position where the usage occurs
    """
    # Find the import position by looking through processed imports
    import_position = find_import_position(processed_imports, alias)
    
    if not import_position:
        # Fallback to usage position if import position not found
        import_position = usage_position
    
    # Create the edge
    usage_edge = UsesImportEdge(
        _from=current_consumer_id,
        _to="",  # Will be resolved by scanner when creating package nodes
        target_symbol=target_symbol,
        target_qname=target_qname,
        alias=alias,
        import_position=import_position,
        usage_positions=[usage_position]
    )
    
    context.results.append(usage_edge)


def find_import_position(
    processed_imports: List, 
    alias: str
) -> Optional[NodePosition]:
    """
    Finds the position of the import statement that introduced the given alias.
    
    Args:
        processed_imports: List of processed import AST nodes
        alias: The alias to search for
        
    Returns:
        NodePosition of the import statement, or None if not found
    """
    for import_node in processed_imports:
        if isinstance(import_node, ast.Import):
            for import_alias in import_node.names:
                used_name = (
                    import_alias.asname 
                    if import_alias.asname 
                    else import_alias.name
                )
                if used_name == alias:
                    return NodePosition(
                        line_no=import_node.lineno,
                        col_offset=import_node.col_offset,
                        end_line_no=getattr(
                            import_node, 'end_lineno', import_node.lineno
                        ),
                        end_col_offset=getattr(
                            import_node, 'end_col_offset', 
                            import_node.col_offset
                        )
                    )
        elif isinstance(import_node, ast.ImportFrom):
            for import_alias in import_node.names:
                used_name = (
                    import_alias.asname 
                    if import_alias.asname 
                    else import_alias.name
                )
                if used_name == alias:
                    return NodePosition(
                        line_no=import_node.lineno,
                        col_offset=import_node.col_offset,
                        end_line_no=getattr(
                            import_node, 'end_lineno', import_node.lineno
                        ),
                        end_col_offset=getattr(
                            import_node, 'end_col_offset', 
                            import_node.col_offset
                        )
                    )
    
    return None 