"""
Dependency resolver utility for finding all dependencies of code elements.
"""
from typing import Set, Union, Dict, Any
from .code_elements import Function, Class
from .package import Package
from ..db import collections as db


class DependencyResolver:
    """
    Utility class to resolve all dependencies of a code element recursively.
    This includes call dependencies, import dependencies, and their
    transitive dependencies.
    """
    
    def __init__(self):
        self.visited_nodes: Set[str] = set()
        self.resolved_dependencies: Dict[
            str, Union[Function, Class, Package]
        ] = {}
    
    def resolve_dependencies(
        self,
        code_element: Union[Function, Class]
    ) -> Dict[str, Union[Function, Class, Package]]:
        """
        Resolves all dependencies of a given code element recursively.
        
        Args:
            code_element: The Function or Class to resolve dependencies for
            
        Returns:
            Dict mapping element IDs to their domain objects
        """
        self.visited_nodes.clear()
        self.resolved_dependencies.clear()
        
        self._resolve_element_dependencies(code_element)
        
        return self.resolved_dependencies
    
    def _resolve_element_dependencies(
        self, 
        element: Union[Function, Class]
    ) -> None:
        """
        Recursively resolves dependencies for a single element.
        
        Args:
            element: The Function or Class to resolve dependencies for
        """
        if element.id in self.visited_nodes:
            return
            
        self.visited_nodes.add(element.id)
        self.resolved_dependencies[element.id] = element
        
        # Resolve call dependencies
        self._resolve_call_dependencies(element)
        
        # Resolve import dependencies
        self._resolve_import_dependencies(element)
    
    def _resolve_call_dependencies(
        self, 
        element: Union[Function, Class]
    ) -> None:
        """
        Resolves call dependencies for a given element.
        
        Args:
            element: The Function or Class to resolve call dependencies for
        """
        # Get function calls
        if hasattr(element, 'get_function_calls'):
            for called_function in element.get_function_calls():
                if called_function.id not in self.visited_nodes:
                    self._resolve_element_dependencies(called_function)
        
        # Get class calls
        if hasattr(element, 'get_class_calls'):
            for called_class in element.get_class_calls():
                if called_class.id not in self.visited_nodes:
                    self._resolve_element_dependencies(called_class)
                    
                    # For classes, also include their methods
                    if hasattr(called_class, 'methods'):
                        for method in called_class.methods:
                            if method.id not in self.visited_nodes:
                                self._resolve_element_dependencies(method)
    
    def _resolve_import_dependencies(
        self, 
        element: Union[Function, Class]
    ) -> None:
        """
        Resolves import dependencies for a given element.
        
        Args:
            element: The Function or Class to resolve import dependencies for
        """
        if not hasattr(element, 'get_imports'):
            return
            
        import_edges = element.get_imports()
        
        for import_edge in import_edges:
            target_node = db.nodes.get(import_edge.to_id)
            if not target_node:
                continue
                
            # Create appropriate domain object based on node type
            if target_node.node_type == 'function':
                target_element = Function(target_node)
                if target_element.id not in self.visited_nodes:
                    self._resolve_element_dependencies(target_element)
                    
            elif target_node.node_type == 'class':
                target_element = Class(target_node)
                if target_element.id not in self.visited_nodes:
                    self._resolve_element_dependencies(target_element)
                    
                    # For classes, also include their methods
                    if hasattr(target_element, 'methods'):
                        for method in target_element.methods:
                            if method.id not in self.visited_nodes:
                                self._resolve_element_dependencies(method)
                                
            elif target_node.node_type == 'package':
                target_element = Package(target_node)
                self.resolved_dependencies[target_element.id] = target_element
    
    def get_dependency_summary(
        self, 
        code_element: Union[Function, Class]
    ) -> Dict[str, Any]:
        """
        Gets a summary of dependencies for a code element.
        
        Args:
            code_element: The Function or Class to get summary for
            
        Returns:
            Dict with categorized dependency information
        """
        dependencies = self.resolve_dependencies(code_element)
        
        summary = {
            'functions': [],
            'classes': [],
            'packages': [],
            'total_count': len(dependencies)
        }
        
        for dep_id, dep_obj in dependencies.items():
            if dep_id == code_element.id:
                continue  # Skip the original element
                
            if isinstance(dep_obj, Function):
                summary['functions'].append({
                    'id': dep_obj.id,
                    'name': dep_obj.name,
                    'qname': dep_obj.qname
                })
            elif isinstance(dep_obj, Class):
                summary['classes'].append({
                    'id': dep_obj.id,
                    'name': dep_obj.name,
                    'qname': dep_obj.qname
                })
            elif isinstance(dep_obj, Package):
                summary['packages'].append({
                    'id': dep_obj.id,
                    'name': dep_obj.name,
                    'qname': dep_obj.qname
                })
        
        return summary 