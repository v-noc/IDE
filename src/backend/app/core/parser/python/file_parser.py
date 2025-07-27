# src/backend/app/core/parser/python/file_parser.py
import ast
from typing import List
from .ast_cache import ASTCache
from .symbol_table import SymbolTable
from .visitors.declaration_visitor import DeclarationVisitor
from .visitors.detail_visitor.dependency_visitor import (
    DependencyVisitor
)
from .visitors.detail_visitor.call_visitor import CallVisitor
from .visitors.detail_visitor.type_inference_visitor import (
    TypeInferenceVisitor
)
from .visitors.detail_visitor.visitor_context import (
    VisitorContext
)
from app.models.node import (
    FunctionNode, ClassNode, NodePosition
)
from app.models.properties import FunctionProperties, ClassProperties
from app.models.base import ArangoBase


class PythonFileParser:
    """
    Orchestrates the two-pass parsing process for a single Python file.
    """
    def __init__(
        self, 
        ast_cache: ASTCache, 
        symbol_table: SymbolTable, 
        project_root: str
    ):
        self.ast_cache = ast_cache
        self.symbol_table = symbol_table
        self.project_root = project_root

    def _get_qname(self, file_path: str, parts: List[str]) -> str:
        """Constructs a fully qualified name."""
        relative_path = file_path.replace(self.project_root, "").lstrip("/")
        module_path = relative_path.replace(".py", "").replace("/", ".")
        return f"{module_path}.{'.'.join(parts)}"

    def run_declaration_pass(
        self, file_path: str, file_content: str
    ) -> List[ArangoBase]:
        """
        Runs the first pass of the analysis to find all high-level 
        declarations. Returns a list of nodes and a dictionary 
        mapping methods to their parent classes.
        """
        try:
            tree = ast.parse(file_content, filename=file_path)
            self.ast_cache.set(file_path, tree)
        except SyntaxError as e:
            # In Phase 5, this will create an AnalysisIssue. For now, log.
            print(f"Syntax error in {file_path}: {e}")
            return []

        visitor = DeclarationVisitor()
        visitor.visit(tree)

        nodes: List[ArangoBase] = []
        
        # Create class nodes
        for class_node in visitor.declared_classes:
            class_qname = self._get_qname(file_path, [class_node.name])
            nodes.append(ClassNode(
                name=class_node.name,
                qname=class_qname,
                properties=ClassProperties(
                    fields=[],
                    position=NodePosition(
                        line_no=class_node.lineno,
                        col_offset=class_node.col_offset,
                        end_line_no=class_node.end_lineno,
                        end_col_offset=class_node.end_col_offset,
                    )
                )
            ))

        # Create method nodes (functions that belong to classes)
        for method_node, parent_class in visitor.methods:
            method_qname = self._get_qname(
                file_path, 
                [parent_class.name, method_node.name]
            )
            nodes.append(FunctionNode(
                name=method_node.name,
                qname=method_qname,
                properties=FunctionProperties(
                    position=NodePosition(
                        line_no=method_node.lineno,
                        col_offset=method_node.col_offset,
                        end_line_no=method_node.end_lineno,
                        end_col_offset=method_node.end_col_offset,
                    )
                )
            ))

        # Create standalone function nodes
        for func_node in visitor.declared_functions:
            func_qname = self._get_qname(file_path, [func_node.name])
            nodes.append(FunctionNode(
                name=func_node.name,
                qname=func_qname,
                properties=FunctionProperties(
                    position=NodePosition(
                        line_no=func_node.lineno,
                        col_offset=func_node.col_offset,
                        end_line_no=func_node.end_lineno,
                        end_col_offset=func_node.end_col_offset,
                    )
                )
            ))
        
        return nodes
    
    def run_detail_pass(
        self, file_path: str, file_id: str
    ) -> List[ArangoBase]:
        """
        Runs the second pass to analyze dependencies and control flow.
        
        This method processes imports and their usage, creating UsesImportEdge
        models that link functions/classes to the symbols they import.
        It also processes function calls, creating CallEdge models that
        link callers to their targets.
        
        Args:
            file_path: The path to the Python file being analyzed
            file_id: The database ID of the file node
            
        Returns:
            List of edge models representing dependencies and calls
        """
        # Get the cached AST for this file
        tree = self.ast_cache.get(file_path)
        if tree is None:
            # If AST is not cached, try to parse the file again
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content, filename=file_path)
                self.ast_cache.set(file_path, tree)
            except (OSError, SyntaxError) as e:
                print(f"Error parsing {file_path} in detail pass: {e}")
                return []
        
        # Create visitor context for the detail analysis pipeline
        context = VisitorContext(
            file_id=file_id,
            ast_tree=tree,
            symbol_table=self.symbol_table
        )
        
        # Initialize the visitor pipeline for Phase 2
        # In future phases, additional visitors will be added here
        
        # Phase 2: Dependency Resolution
        dependency_visitor = DependencyVisitor(context)
        dependency_visitor.visit(tree)
        
        # Phase 2: Call Resolution
        call_visitor = CallVisitor(context)
        call_visitor.visit(tree)
        
        # Phase 4: Type Inference (enabled now)
        type_inference_visitor = TypeInferenceVisitor(context)
        type_inference_visitor.visit(tree)
        
        # Future phases will add:
        # Phase 3: Control Flow Analysis
        # control_flow_visitor = ControlFlowVisitor(context)
        # control_flow_visitor.visit(tree)
        
        return context.results
    
    def clear_cache(self, file_path: str) -> None:
        """
        Clears the cached AST for a specific file.
        Useful during development when files are modified.
        
        Args:
            file_path: The path to the file whose cache should be cleared
        """
        self.ast_cache.clear(file_path)
    
    def get_cached_files(self) -> List[str]:
        """
        Gets all files that have cached ASTs.
        
        Returns:
            List of file paths with cached ASTs
        """
        return list(self.ast_cache._cache.keys())
