from typing import List, Optional, Dict
from loguru import logger

from .qname_resolver import QNameResolver
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SymbolModel, SymbolType


class MROCalculator:
    def __init__(self, repo: ScopeManagerRepository, qname_resolver: QNameResolver):
        self.repo = repo
        self.qname_resolver = qname_resolver
        self._mro_cache: Dict[str, List[str]] = {}

    def calculate_all(self):
        """
        Calculates and caches the MRO for all classes in the graph.
        """
        classes = self.repo.symbols.get_by_type(SymbolType.CLASS.value)
        for class_symbol in classes:
            qname = self.qname_resolver.get_qname_for_symbol(class_symbol.id)

            if qname:
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

        class_symbol = self.qname_resolver.resolve_qname(class_qname)
        if not class_symbol:
            # Fail-safe: treat unknown/external classes as a simple leaf in MRO
            logger.warning(
                f"MRO: class '{class_qname}' not found;"
            )

            return mro

        # Check if MRO is already computed and stored in DB
        if class_symbol.attrs and 'mro' in class_symbol.attrs:
            self._mro_cache[class_qname] = class_symbol.attrs['mro']
            return class_symbol.attrs['mro']

        # Get base classes from attrs
        base_classes = class_symbol.attrs.get(
            'base_classes', []) if class_symbol.attrs else []

        # The merge operation is the core of the C3 algorithm.
        try:
            mro = self._merge(
                [[class_qname]] +
                [self.get_mro(base).copy() for base in base_classes] +
                [base_classes.copy()]
            )
        except TypeError:
            # Fallback for inconsistent MRO
            logger.error(f"MRO: Inconsistent hierarchy for {class_qname}")
            mro = [class_qname] + base_classes

        self._mro_cache[class_qname] = mro

        # Update the symbol in the DB with the calculated MRO
        # We need to be careful about session management here.
        # Ideally, we should update the object attached to the session.
        if not class_symbol.attrs:
            class_symbol.attrs = {}

        # Create a new dict to ensure SQLAlchemy detects the change
        new_attrs = class_symbol.attrs.copy()
        new_attrs['mro'] = mro
        class_symbol.attrs = new_attrs

        # We rely on the caller to commit the session

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


class MethodResolver:
    def __init__(self, repo: ScopeManagerRepository, qname_resolver: QNameResolver, mro_calculator: MROCalculator):
        self.repo = repo
        self.qname_resolver = qname_resolver
        self.mro_calculator = mro_calculator

    def resolve_method(self, class_qname: str, method_name: str) -> Optional[SymbolModel]:
        """
        Finds the symbol for a method by searching the MRO of a given class.

        This handles normal method calls like `instance.method()`.
        """
        mro = self.mro_calculator.get_mro(class_qname)

        for base_qname in mro:
            base_symbol = self.qname_resolver.resolve_qname(base_qname)
            if not base_symbol or not base_symbol.defines_scope_id:
                continue

            # Look for method in the class scope
            method_symbol = self.repo.symbols.get_by_name_in_scope(
                method_name, base_symbol.defines_scope_id
            )

            if method_symbol:
                return method_symbol

        return None

    def resolve_super_call(self, class_qname: str, method_name: str) -> Optional[SymbolModel]:
        """
        Finds the symbol for a method in the MRO, starting *after* the current class.

        This handles `super().method()` calls.
        """
        mro = self.mro_calculator.get_mro(class_qname)

        # Find the position of the current class in its own MRO.
        try:
            current_class_index = mro.index(class_qname)
        except ValueError:
            return None  # Should not happen in a valid MRO

        # Start the search from the *next* class in the MRO.
        search_mro = mro[current_class_index + 1:]

        for base_qname in search_mro:
            base_symbol = self.qname_resolver.resolve_qname(base_qname)
            if not base_symbol or not base_symbol.defines_scope_id:
                continue

            method_symbol = self.repo.symbols.get_by_name_in_scope(
                method_name, base_symbol.defines_scope_id
            )

            if method_symbol:
                return method_symbol

        return None


class InheritanceResolver:
    def __init__(self, repo: ScopeManagerRepository, qname_resolver: QNameResolver):
        self.mro_calculator = MROCalculator(repo, qname_resolver)
        self.method_resolver = MethodResolver(
            repo, qname_resolver, self.mro_calculator)
