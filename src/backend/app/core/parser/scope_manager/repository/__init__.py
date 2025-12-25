from typing import List, Optional

from ..db import DBConnectionManager
from ..models import ScopeModel, CallSiteModel

from .scope_repository import ScopeRepository as ScopeCRUDRepository
from .call_site_repository import CallSiteRepository
from .hierarchy_repository import HierarchyRepository
from .query_repository import QueryRepository
from .deletion_repository import DeletionRepository


class ScopeRepository:
    """
    Main repository that composes all domain-specific repositories.
    Maintains backward compatibility with the original single-class interface.
    """

    def __init__(self, db_manager: DBConnectionManager):
        # Initialize domain-specific repositories
        self._scope_repo = ScopeCRUDRepository(db_manager)
        self._call_site_repo = CallSiteRepository(db_manager)
        self._hierarchy_repo = HierarchyRepository(db_manager)
        self._query_repo = QueryRepository(db_manager)
        self._deletion_repo = DeletionRepository(db_manager)

    # Scope CRUD operations - delegate to ScopeCRUDRepository
    async def create_scope(self, scope: ScopeModel) -> None:
        """Create a Scope node."""
        await self._scope_repo.create_scope(scope)

    async def update_scope(self, scope: ScopeModel) -> None:
        """Update an existing Scope node's properties."""
        await self._scope_repo.update_scope(scope)

    async def batch_update_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch update multiple scopes efficiently using Neo4j UNWIND."""
        await self._scope_repo.batch_update_scopes(scopes)

    async def get_scope_by_id(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a Scope by ID."""
        return await self._scope_repo.get_scope_by_id(scope_id)

    async def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by its qualified name."""
        return await self._scope_repo.get_scope_by_qname(qname)

    async def batch_get_scopes_by_qnames(
        self, qnames: List[str]
    ) -> dict[str, ScopeModel]:
        """
        Batch get scopes by their qualified names.
        Returns a dict mapping qname -> ScopeModel.
        """
        return await self._scope_repo.batch_get_scopes_by_qnames(qnames)

    async def batch_get_scopes_by_ids(
        self, scope_ids: List[str]
    ) -> dict[str, ScopeModel]:
        """
        Batch get scopes by their IDs.
        Returns a dict mapping id -> ScopeModel.
        """
        return await self._scope_repo.batch_get_scopes_by_ids(scope_ids)

    async def batch_create_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch create multiple scopes efficiently using Neo4j UNWIND."""
        await self._scope_repo.batch_create_scopes(scopes)

    # Call Site operations - delegate to CallSiteRepository
    async def create_call_site(
        self,
        caller_id: str,
        callee_id: Optional[str],
        call_site: CallSiteModel,
        prev_call_site_id: Optional[str] = None,
    ) -> None:
        """Create a call site node and link it to caller/callee."""
        await self._call_site_repo.create_call_site(
            caller_id, callee_id, call_site, prev_call_site_id
        )

    async def batch_create_call_sites(
        self,
        call_sites: List[dict],
    ) -> None:
        """Batch create multiple call sites efficiently using Neo4j UNWIND."""
        await self._call_site_repo.batch_create_call_sites(call_sites)

    async def clear_calls_from_scope(self, scope_id: str) -> None:
        """Delete all call sites originating from the given scope."""
        await self._call_site_repo.clear_calls_from_scope(scope_id)

    async def get_call_chain(self, call_site_id: str) -> List[CallSiteModel]:
        """Get the full call chain starting from a call site."""
        return await self._call_site_repo.get_call_chain(call_site_id)

    async def get_call_chain_roots(
        self,
        target_scope_id: Optional[str] = None,
    ) -> List[CallSiteModel]:
        """Get call sites that start a chain (no incoming NEXT_IN_CHAIN)."""
        return await self._call_site_repo.get_call_chain_roots(target_scope_id)

    # Hierarchy operations - delegate to HierarchyRepository
    async def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Create CONTAINS relationship."""
        await self._hierarchy_repo.link_parent_child(parent_id, child_id)

    async def batch_link_parent_child(
        self, relationships: List[dict[str, str]]
    ) -> None:
        """Batch create CONTAINS relationships."""
        await self._hierarchy_repo.batch_link_parent_child(relationships)

    async def batch_relink_parent_child(
        self, relationships: List[dict[str, str]]
    ) -> None:
        """Batch relink CONTAINS relationships (ensure exactly one parent per child)."""
        await self._hierarchy_repo.batch_relink_parent_child(relationships)

    async def relink_parent_child(self, new_parent_id: str, child_id: str) -> None:
        """Replace any existing parent CONTAINS links for child_id with new_parent_id."""
        await self._hierarchy_repo.relink_parent_child(new_parent_id, child_id)

    async def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all direct children of a scope."""
        return await self._hierarchy_repo.get_children(parent_id)

    # Query operations - delegate to QueryRepository
    async def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        return await self._query_repo.get_all_scopes()

    async def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        return await self._query_repo.get_all_file_scopes()

    async def get_all_folder_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FOLDER."""
        return await self._query_repo.get_all_folder_scopes()

    # Deletion operations - delegate to DeletionRepository
    async def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        await self._deletion_repo.delete_scope(scope_id)

    async def delete_file_scope(self, file_path: str) -> None:
        """Delete a file scope and its children."""
        await self._deletion_repo.delete_file_scope(file_path)

    async def batch_delete_scopes(self, root_scope_ids: List[str]) -> None:
        """Batch delete multiple scopes and all their children/relationships."""
        await self._deletion_repo.batch_delete_scopes(root_scope_ids)

    async def batch_delete_file_scopes(self, file_paths: List[str]) -> None:
        """Batch delete multiple file scopes and all their children/relationships."""
        await self._deletion_repo.batch_delete_file_scopes(file_paths)

    async def clear_db(self) -> None:
        """Clear all nodes and relationships."""
        await self._deletion_repo.clear_db()
