from .storage.models import ScopeModel, ScopeType
from .storage.repository.repos import ScopeManagerRepository
from .resolver.scope_resolver import ScopeResolver
from .resolver.symbol_resolver import SymbolResolver
from .resolver.qname_resolver import QNameResolver
from .storage.database import DatabaseManager
from .resolver import Resolver
from .writer import Writer


class ScopeManager:
    """
    Manages the scope hierarchy and symbol resolution.
    """

    def __init__(self):
        self.root_scope_id = None
        self.current_scope_id = None

    def create_root_scope(self, name: str = "__main__", file_path: str = "") -> ScopeModel:
        """
        Create the root scope for the project.
        """

        self.project_name = name
        self.db_manager = DatabaseManager(name)
        self.session = self.db_manager.get_session()

        self.repo = ScopeManagerRepository(self.session)

        self.resolver = Resolver(self.repo)
        self.writer = Writer(self.repo)

        root_scope = self.repo.scopes.get_root()

        if root_scope:
            self.root_scope_id = root_scope.id
            self.current_scope_id = root_scope.id
            return root_scope

        source_unit = self.writer.source_writer.create_source(
            file_path=file_path,
        )

        root_scope = self.writer.scope_writer.create_scope(
            name=name,
            scope_type=ScopeType.PROJECT,
            source_unit_id=source_unit.id,
            is_root=True,
        )
        self.root_scope_id = root_scope.id
        self.current_scope_id = root_scope.id
        return root_scope

    def enter_scope(self, name: str, scope_type: ScopeType, file_path: str) -> ScopeModel:
        """
        Enters a new nested scope and creates a corresponding symbol
        in the parent scope if necessary (for functions and classes).
        """
        if not self.current_scope_id:
            raise ValueError(
                "Cannot enter scope without a root. Call create_root_scope() first."
            )

        source_unit = self.writer.source_writer.create_source(
            file_path=file_path,
        )

        scope = self.writer.scope_writer.create_scope(
            name=name,
            scope_type=scope_type,
            source_unit_id=source_unit.id,
            parent_id=self.current_scope_id,
        )
        self.current_scope_id = scope.id
        return scope

    def exit_scope(self) -> ScopeModel:
        """
        Exits the current scope and moves to its parent.
        """
        if not self.current_scope_id:
            raise ValueError(
                "Cannot exit scope without a current scope. Call enter_scope() first."
            )
        parent_scope = self.repo.scopes.get_by_id(self.current_scope_id).parent
        self.current_scope_id = parent_scope.id
        return parent_scope

    def enter_scope_by_scope_id(self, scope_id: str) -> ScopeModel:
        """
        Enters a new nested scope and creates a corresponding symbol
        in the parent scope if necessary (for functions and classes).
        """
        if not self.current_scope_id:
            raise ValueError(
                "Cannot enter scope without a root. Call create_root_scope() first."
            )
        scope = self.repo.scopes.get_by_id(scope_id)
        if not scope:
            raise ValueError(
                "Scope not found. Call enter_scope() first."
            )
        self.current_scope_id = scope.id
        return scope
