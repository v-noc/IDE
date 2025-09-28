from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.ast.models import CallSchema


class CallHandler:
    """Handles call-related nodes"""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def handle_call_node(self, node: CallSchema):
        """Process a call node"""
        pass
