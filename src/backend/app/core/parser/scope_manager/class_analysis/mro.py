from .model import InheritanceGraph
from typing import List, Dict
from loguru import logger


class MROCalculator:
    def __init__(self, inheritance_graph: InheritanceGraph):
        self.inheritance_graph = inheritance_graph
        self._mro_cache: Dict[str, List[str]] = {}

    def calculate_all(self):
        """
        Calculates and caches the MRO for all classes in the graph.
        """
        for qname in self.inheritance_graph.classes:
            try:
                self.get_mro(qname)
            except Exception:
                pass

    def get_mro(self, class_qname: str) -> List[str]:
        """
        Returns the MRO for a given class, computing it if not already cached.
        """
        if class_qname in self._mro_cache:
            return self._mro_cache[class_qname]

        try:
            class_node = self.inheritance_graph.get_class(class_qname)
        except Exception:
            # Fail-safe: treat unknown/external classes as a simple leaf in MRO
            logger.warning(
                f"MRO: class '{class_qname}' not found; treating as external."
            )
            mro = [class_qname]
            self._mro_cache[class_qname] = mro
            return mro

        # The merge operation is the core of the C3 algorithm.
        mro = self._merge(
            [[class_qname]] +
            # --- KEY CHANGE ---
            # We must pass COPIES of the MRO lists to the merge function,
            # because the merge function mutates the lists it receives.
            # Without .copy(), we would be destroying our cached results.
            [self.get_mro(base).copy() for base in class_node.base_classes] +
            [class_node.base_classes.copy()]
        )

        self._mro_cache[class_qname] = mro
        class_node.mro_list = mro  # Store it on the node as well
        return mro

    def _merge(self, sequences: List[List[str]]) -> List[str]:
        """
        Performs the C3 merge operation.
        """
        result: List[str] = []

        while True:
            sequences = [s for s in sequences if s]  # Strip empty sequences
            if not sequences:
                return result

            head = self._find_merge_head(sequences)
            if not head:
                raise TypeError(
                    "Cannot create a consistent method resolution order "
                    "(MRO)"
                )

            result.append(head)

            # Remove the found head from the head of all sequences
            for seq in sequences:
                if seq[0] == head:
                    del seq[0]

    def _find_merge_head(self, sequences: List[List[str]]) -> str | None:
        """
        Finds a valid head for the merge operation.
        A head is valid if it does not appear in the tail of any other
        sequence.
        """
        for seq in sequences:
            head = seq[0]
            is_valid_head = True
            for other_seq in sequences:
                if head in other_seq[1:]:
                    is_valid_head = False
                    break
            if is_valid_head:
                return head
        return None
