from .model import InheritanceGraph

from typing import List, Dict, Optional

from app.core.parser.scope_manager.core.symbol import Symbol


class MethodResolver:
    def __init__(self, inheritance_graph: InheritanceGraph):
        self.inheritance_graph = inheritance_graph

    def resolve_method(self, class_qname: str, method_name: str) -> str:
        """
        Finds the symbol for a method by searching the MRO of a given class.

        This handles normal method calls like `instance.method()`.
        """
        class_node = self.inheritance_graph.get_class(class_qname)

        if not class_node.mro_list:
            raise RuntimeError(
                f"MRO not calculated for class '{class_qname}'.")

        for base_qname in class_node.mro_list:
            base_node = self.inheritance_graph.get_class(base_qname)

            if method_name in base_node.scope.symbols:
                symbol = base_node.scope.symbols[method_name]
                # You might want to add a check here to ensure it's a function/method symbol
                return symbol

        return None

    def resolve_super_call(self, class_qname: str, method_name: str) -> Optional[Symbol]:
        """
        Finds the symbol for a method in the MRO, starting *after* the current class.

        This handles `super().method()` calls.
        """
        class_node = self.inheritance_graph.get_class(class_qname)
        if not class_node.mro_list:
            raise RuntimeError(
                f"MRO not calculated for class '{class_qname}'.")

        # Find the position of the current class in its own MRO.
        try:
            current_class_index = class_node.mro_list.index(class_qname)
        except ValueError:
            return None  # Should not happen in a valid MRO

        # Start the search from the *next* class in the MRO.
        search_mro = class_node.mro_list[current_class_index + 1:]

        for base_qname in search_mro:
            base_node = self.inheritance_graph.get_class(base_qname)
            if method_name in base_node.scope.symbols:
                return base_node.scope.symbols[method_name]

        return None
