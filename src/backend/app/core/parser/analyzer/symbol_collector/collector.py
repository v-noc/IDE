from app.core.parser.analyzer.symbol_table import SymbolTable
from app.core.parser.analyzer.file_navigator import FileContainer


class SymbolCollector:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def collect_symbols(self, file_node: FileContainer):
        pass
