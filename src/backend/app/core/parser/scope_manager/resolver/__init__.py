
from ..storage.repository.repos import ScopeManagerRepository
from .scope_resolver import ScopeResolver
from .symbol_resolver import SymbolResolver
from .qname_resolver import QNameResolver
from .assignment_resolver import AssignmentResolver
from .inheritance_resolver import InheritanceResolver


class Resolver:

    """
    Resolves names in the scope hierarchy.
    """

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

        self.scope_resolver = ScopeResolver(self.repo)
        self.symbol_resolver = SymbolResolver(self.repo, self.scope_resolver)
        self.qname_resolver = QNameResolver(
            self.repo, self.scope_resolver, self.symbol_resolver)

        self.assignment_resolver = AssignmentResolver(
            self.repo, self.scope_resolver, self.symbol_resolver)

        self.inheritance_resolver = InheritanceResolver(
            self.repo, self.qname_resolver)
