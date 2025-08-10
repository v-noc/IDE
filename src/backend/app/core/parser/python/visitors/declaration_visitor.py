# src/backend/app/core/parser/python/visitors/declaration_visitor.py
import ast
from typing import List, Union, Optional
from dataclasses import dataclass


@dataclass
class HierarchicalNode:
    """Represents a node in the hierarchical structure with parent-child 
    relationships"""
    ast_node: Union[ast.FunctionDef, ast.ClassDef]
    node_type: str  # 'function' or 'class'
    parent: Optional['HierarchicalNode'] = None
    children: List['HierarchicalNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class DeclarationVisitor(ast.NodeVisitor):
    """
    A visitor that collects all function, class, and import declarations
    from a file's AST and creates a hierarchical structure.
    """
    def __init__(self):
        self.imports: List[Union[ast.Import, ast.ImportFrom]] = []
        self.root_nodes: List[HierarchicalNode] = []  # Top-level nodes
        # Current nesting context
        self._context_stack: List[HierarchicalNode] = []
        
    def _create_hierarchical_node(
        self, 
        ast_node: Union[ast.FunctionDef, ast.ClassDef], 
        node_type: str
    ) -> HierarchicalNode:
        """Creates a hierarchical node and links it to its parent"""
        parent = self._context_stack[-1] if self._context_stack else None
        
        hierarchical_node = HierarchicalNode(
            ast_node=ast_node,
            node_type=node_type,
            parent=parent
        )
        
        if parent:
            parent.children.append(hierarchical_node)
        else:
            self.root_nodes.append(hierarchical_node)
            
        return hierarchical_node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Identifies a function definition and creates hierarchical structure"""
        hierarchical_node = self._create_hierarchical_node(node, 'function')
        
        # Push this function onto the context stack for nested elements
        self._context_stack.append(hierarchical_node)
        
        # Visit the function body to find nested functions and classes
        self.generic_visit(node)
        
        # Pop the function from the context stack when done
        self._context_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Identifies a class definition and creates hierarchical structure"""
        hierarchical_node = self._create_hierarchical_node(node, 'class')
        
        # Push this class onto the context stack for nested elements
        self._context_stack.append(hierarchical_node)
        
        # Visit the class body to find methods and nested classes
        self.generic_visit(node)
        
        # Pop the class from the context stack when done
        self._context_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        """Identifies an 'import ...' statement."""
        self.imports.append(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Identifies a 'from ... import ...' statement."""
        self.imports.append(node)
        
    def get_all_nodes_flat(self) -> List[HierarchicalNode]:
        """Returns all nodes in a flat list for backward compatibility"""
        def collect_nodes(node: HierarchicalNode) -> List[HierarchicalNode]:
            result = [node]
            for child in node.children:
                result.extend(collect_nodes(child))
            return result
        
        all_nodes = []
        for root_node in self.root_nodes:
            all_nodes.extend(collect_nodes(root_node))
        return all_nodes
