# src/backend/app/core/parser/python/file_parser.py
import ast
from typing import List
from .ast_cache import ASTCache
from .symbol_table import SymbolTable
from .visitors.declaration_visitor import DeclarationVisitor
from ....models.node import FunctionNode, ClassNode, NodePosition
from ....models.properties import FunctionProperties, ClassProperties
from ....models.base import ArangoBase

class PythonFileParser:
    """
    Orchestrates the two-pass parsing process for a single Python file.
    """
    def __init__(self, ast_cache: ASTCache, symbol_table: SymbolTable, project_root: str):
        self.ast_cache = ast_cache
        self.symbol_table = symbol_table
        self.project_root = project_root

    def _get_qname(self, file_path: str, parts: List[str]) -> str:
        """Constructs a fully qualified name."""
        relative_path = file_path.replace(self.project_root, "").lstrip("/")
        module_path = relative_path.replace(".py", "").replace("/", ".")
        return f"{module_path}.{'.'.join(parts)}"

    def run_declaration_pass(self, file_path: str, file_content: str) -> List[ArangoBase]:
        """
        Runs the first pass of the analysis to find all high-level declarations.
        """
        try:
            tree = ast.parse(file_content, filename=file_path)
            self.ast_cache.set(file_path, tree)
        except SyntaxError as e:
            # In Phase 5, this will create an AnalysisIssue. For now, we just log.
            print(f"Syntax error in {file_path}: {e}")
            return []

        visitor = DeclarationVisitor()
        visitor.visit(tree)

        nodes: List[ArangoBase] = []
        processed_funcs = set()

        for class_node in visitor.declared_classes:
            class_qname = self._get_qname(file_path, [class_node.name])
            nodes.append(ClassNode(
                name=class_node.name,
                qname=class_qname,
                properties=ClassProperties(
                    position=NodePosition(
                        line_no=class_node.lineno,
                        col_offset=class_node.col_offset,
                        end_line_no=class_node.end_lineno,
                        end_col_offset=class_node.end_col_offset,
                    )
                )
            ))

            for func_node in visitor.declared_functions:
                # Check if the function is a method of the current class
                if (func_node.lineno >= class_node.lineno and
                        func_node.end_lineno <= class_node.end_lineno):
                    
                    method_qname = self._get_qname(file_path, [class_node.name, func_node.name])
                    nodes.append(FunctionNode(
                        name=func_node.name,
                        qname=method_qname,
                        properties=FunctionProperties(
                            position=NodePosition(
                                line_no=func_node.lineno,
                                col_offset=func_node.col_offset,
                                end_line_no=func_node.end_lineno,
                                end_col_offset=func_node.end_col_offset,
                            )
                        )
                    ))
                    processed_funcs.add(func_node)

        # Process remaining functions (not methods)
        for func_node in visitor.declared_functions:
            if func_node not in processed_funcs:
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
    def run_detail_pass(self, file_path: str) -> List[ArangoBase]:
        """
        Runs the second pass to analyze dependencies and control flow.
        (To be implemented in later phases)
        """
        return []
