"""
Main dependency visitor orchestrator.

This module provides the main DependencyVisitor class that orchestrates
all the dependency analysis components: import processing, usage detection,
and context management.
"""

import ast
from ..visitor_context import VisitorContext
from .import_processor import ImportProcessor
from .context_manager import DependencyContextManager
from .usage_detector import UsageDetector


class DependencyVisitor(ast.NodeVisitor):
    """
    A visitor to resolve all import statements and create dependency edges.
    
    This visitor processes import statements and their usage throughout the 
    code, differentiating between local modules and external packages, and 
    creating UsesImportEdge models to represent these dependencies.
    
    This is the main orchestrator that coordinates the specialized components:
    - ImportProcessor: Handles import statement processing
    - DependencyContextManager: Manages function/class context
    - UsageDetector: Detects symbol usage
    """
    
    def __init__(self, context: VisitorContext):
        self.context = context
        
        # Initialize specialized components
        self.import_processor = ImportProcessor(context)
        self.context_manager = DependencyContextManager(context)
        self.usage_detector = UsageDetector(
            context=context,
            get_current_consumer_id_func=(
                self.context_manager.get_current_consumer_id
            ),
            get_processed_imports_func=(
                self.import_processor.get_processed_imports
            )
        )
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Sets the context for which function is currently being analyzed.
        This determines the 'from' part of UsesImportEdge.
        
        Args:
            node: The ast.FunctionDef node to visit
        """
        self.context_manager.visit_function_def(
            node=node,
            visit_body_callback=self.generic_visit
        )
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Sets the context for which class is currently being analyzed.
        
        Args:
            node: The ast.ClassDef node to visit
        """
        self.context_manager.visit_class_def(
            node=node,
            visit_body_callback=self.generic_visit
        )
    
    def visit_Import(self, node: ast.Import) -> None:
        """
        Processes 'import module' statements and registers them in the 
        symbol table.
        
        Args:
            node: The ast.Import node to visit
        """
        self.import_processor.process_import(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Processes 'from module import symbol' statements and registers them 
        in the symbol table.
        
        Args:
            node: The ast.ImportFrom node to visit
        """
        self.import_processor.process_import_from(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        """
        Handles usage of simple imported names, like 'Request' in 
        'from fastapi import Request'.
        
        Args:
            node: The ast.Name node to visit
        """
        self.usage_detector.detect_name_usage(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """
        Handles usage of aliased imports, like 'np.array' where 'np' is an 
        alias for 'numpy'.
        
        Args:
            node: The ast.Attribute node to visit
        """
        self.usage_detector.detect_attribute_usage(
            node=node,
            visit_callback=self.generic_visit
        )
    
    def get_analysis_summary(self) -> dict:
        """
        Returns a summary of the dependency analysis results.
        
        Returns:
            Dictionary containing analysis statistics
        """
        processed_imports = self.import_processor.get_processed_imports()
        has_consumer = self.context_manager.has_current_consumer()
        
        return {
            "total_imports_processed": len(processed_imports),
            "import_types": {
                "regular_imports": sum(
                    1 for imp in processed_imports 
                    if isinstance(imp, ast.Import)
                ),
                "from_imports": sum(
                    1 for imp in processed_imports 
                    if isinstance(imp, ast.ImportFrom)
                )
            },
            "has_active_consumer": has_consumer,
            "total_edges_created": len(self.context.results)
        } 