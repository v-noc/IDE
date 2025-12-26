import asyncio
from .db import DBConnectionManager
from .repository import ScopeRepository
from .models import ScopeModel, CallSiteModel, ScopeType
from typing import Optional, List
import uuid


class ScopeManager:
    """
    Facade/Service layer for managing scopes and call sites.
    Provides high-level operations for creating, querying, and managing code structure.
    """

    def __init__(self, project_name: str, db_path: Optional[str] = None):
        self.db_manager = DBConnectionManager(project_name, db_path)
        self.repository = ScopeRepository(self.db_manager)
        self.semaphore = asyncio.Semaphore(1)

    def close(self) -> None:
        """Close the database connection."""
        self.db_manager.close()

    # Scope Management

    async def initialize(self) -> None:
        """Initialize the database."""
        await self.db_manager._initialize_schema()

    async def create_scope(
        self,
        name: str,
        qname: str,
        scope_type: ScopeType,
        file_path: str,
        start_line: int,
        start_col: int,
        end_line: int,
        end_col: int,
        mro: List[str] = None,
        scope_id: Optional[str] = None,
        checksum: Optional[str] = None,
    ) -> ScopeModel:
        """Create a new scope."""
        async with self.semaphore:
            scope = ScopeModel(
                id=scope_id or str(uuid.uuid4()),
                name=name,
                qname=qname,
                type=scope_type,
                file_path=file_path,
                start_line=start_line,
                start_col=start_col,
                end_line=end_line,
                end_col=end_col,
                mro=mro or [],
                checksum=checksum,
            )
            await self.repository.create_scope(scope)
            return scope

    async def update_scope(self, scope: ScopeModel) -> ScopeModel:
        """Update an existing scope."""
        async with self.semaphore:
            await self.repository.update_scope(scope)
            return scope

    async def batch_get_scopes_by_ids(self, scope_ids: List[str]) -> dict[str, ScopeModel]:
        """Batch get scopes by their IDs. Returns a dict mapping id -> ScopeModel."""

        return await self.repository.batch_get_scopes_by_ids(scope_ids)

    async def batch_update_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch update multiple scopes efficiently."""
        async with self.semaphore:
            await self.repository.batch_update_scopes(scopes)

    async def get_scope(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a scope by ID."""

        return await self.repository.get_scope_by_id(scope_id)

    async def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by qualified name."""
        return await self.repository.get_scope_by_qname(qname)

    async def delete_scope(self, scope_id: str) -> None:
        """Delete a scope and its relationships."""
        async with self.semaphore:
            await self.repository.delete_scope(scope_id)

    async def batch_delete_scopes(self, root_scope_ids: List[str]) -> None:
        """Batch delete multiple scopes and all their children/relationships."""
        await self.repository.batch_delete_scopes(root_scope_ids)

    async def delete_file_scope(self, file_path: str) -> None:
        """Delete a file scope by its path."""
        async with self.semaphore:
            await self.repository.delete_file_scope(file_path)

    async def batch_delete_file_scopes(self, file_paths: List[str]) -> None:
        """Batch delete multiple file scopes and all their children/relationships."""
        async with self.semaphore:
            await self.repository.batch_delete_file_scopes(file_paths)

    async def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        return await self.repository.get_all_scopes()

    async def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        return await self.repository.get_all_file_scopes()

    async def get_all_folder_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FOLDER."""
        return await self.repository.get_all_folder_scopes()

    async def get_scopes_by_file_path(self, file_path: str) -> List[ScopeModel]:
        """Get scopes by file path (should be mainly the file scope itself)."""
        return await self.repository.get_scopes_by_file_path(file_path)

    # Hierarchy Management

    async def link_parent_child(self, parent_id: str, child_id: str) -> None:
        """Link a parent scope to a child scope (e.g., Class contains Function)."""
        async with self.semaphore:
            await self.repository.link_parent_child(parent_id, child_id)

    async def relink_parent_child(self, new_parent_id: str, child_id: str) -> None:
        """
        Replace any existing incoming CONTAINS relationship(s) for child_id with
        a single link from new_parent_id.
        """
        async with self.semaphore:
            await self.repository.relink_parent_child(new_parent_id, child_id)

    async def batch_get_scopes_by_qnames(self, qnames: List[str]) -> dict[str, ScopeModel]:
        """Batch get scopes by their qualified names. Returns a dict mapping qname -> ScopeModel."""
        return await self.repository.batch_get_scopes_by_qnames(qnames)

    async def batch_create_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch create multiple scopes efficiently."""
        async with self.semaphore:
            await self.repository.batch_create_scopes(scopes)

    async def batch_link_parent_child(self, relationships: List[dict[str, str]]) -> None:
        """Batch link parent-child relationships. relationships is a list of dicts with 'parent_id' and 'child_id' keys."""
        async with self.semaphore:
            await self.repository.batch_link_parent_child(relationships)

    async def batch_relink_parent_child(
        self, relationships: List[dict[str, str]]
    ) -> None:
        """
        Batch relink parent-child relationships.
        For each child_id, remove existing incoming CONTAINS edges and create a new one
        from parent_id.
        """
        async with self.semaphore:
            await self.repository.batch_relink_parent_child(relationships)

    async def get_children(self, parent_id: str) -> List[ScopeModel]:
        """Get all children of a scope."""
        return await self.repository.get_children(parent_id)

    async def get_descendants(self, root_id: str) -> List[ScopeModel]:
        """Get all descendants of a scope."""
        return await self.repository.get_descendants(root_id)

    # Call Site Management

    async def create_call(
        self,
        caller_id: str,
        line: int,
        col: int,
        name: Optional[str] = None,
        callee_id: Optional[str] = None,
        prev_call_site_id: Optional[str] = None,
    ) -> CallSiteModel:
        """Create a call site linking caller to callee (if resolved), optionally chained."""
        async with self.semaphore:
            call_site = CallSiteModel(
                id=str(uuid.uuid4()),
                line=line,
                col=col,
                name=name,
            )
            await self.repository.create_call_site(
                caller_id, callee_id, call_site, prev_call_site_id)
            return call_site

    async def batch_create_calls(
        self,
        call_sites: List[dict],
    ) -> List[CallSiteModel]:
        """
        Batch create multiple call sites efficiently.

        Args:
            call_sites: List of dicts with keys:
                - caller_id: str
                - line: int
                - col: int
                - name: Optional[str]
                - callee_id: Optional[str]
                - prev_call_site_id: Optional[str]

        Returns:
            List of created CallSiteModel instances
        """
        if not call_sites:
            return []

        # Create CallSiteModel instances
        async with self.semaphore:
            created_call_sites = []
            batch_data = []
            for item in call_sites:
                call_site = CallSiteModel(
                    id=str(uuid.uuid4()),
                    line=item["line"],
                    col=item["col"],
                    name=item.get("name"),
                )
                created_call_sites.append(call_site)
                batch_data.append({
                    "call_site": call_site,
                    "caller_id": item["caller_id"],
                    "callee_id": item.get("callee_id"),
                    "prev_call_site_id": item.get("prev_call_site_id"),
                })

            # Batch insert
            await self.repository.batch_create_call_sites(batch_data)
            return created_call_sites

    async def get_root_calls_from(
        self, caller_id: str, include_children: bool = False
    ) -> List[dict]:
        """
        Get root calls made from a scope (calls with no previous call site
        parent).

        Args:
            caller_id: The scope ID to get root calls from
            include_children: If True, also fetch calls inside each callee
                             scope and attach them as a 'children' attribute

        Returns:
            List of call info dicts with 'call_site' and 'callee' keys.
            If include_children=True, each dict also has a 'children' key
            containing calls inside the callee scope.
        """
        if include_children:
            # Fetch root calls with their nested children in one query
            async with self.semaphore:
                result = await self.db_manager.connection.execute(
                    """
                    MATCH (caller:Scope {id: $caller_id})
                        -[:HAS_CALL_SITE]->(cs:CallSite)
                    WHERE NOT EXISTS {
                        MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(cs)
                    }
                    OPTIONAL MATCH (cs)-[:TARGETS]->(callee:Scope)
                    WITH cs, callee
                    OPTIONAL MATCH (cs)-[:TARGETS]->(callee:Scope)
                        -[:HAS_CALL_SITE]->(inner_call:CallSite)
                    OPTIONAL MATCH (inner_call)-[:TARGETS]->(inner_callee:Scope)
                    WITH cs, callee,
                        collect(DISTINCT {
                            inner_call: inner_call,
                            inner_callee: inner_callee
                        }) AS children_data
                    RETURN cs, callee, children_data
                    """,
                    {"caller_id": caller_id}
                )
        else:
            async with self.semaphore:
                result = await self.db_manager.connection.execute(
                    """
                    MATCH (caller:Scope {id: $caller_id})-[:HAS_CALL_SITE]->(cs:CallSite)
                    WHERE NOT EXISTS { MATCH (:CallSite)-[:NEXT_IN_CHAIN]->(cs) }
                    OPTIONAL MATCH (cs)-[:TARGETS]->(callee:Scope)
                    RETURN cs, callee
                    """,
                    {"caller_id": caller_id}
                )

        calls = []
        for row in result:
            cs_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            call_info = {
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                    name=cs_node.get("name"),
                ),
                "callee": callee,
            }

            # If include_children, process children data
            if include_children and len(row) > 2:
                children_data = row[2]
                children = []
                for child_item in children_data:
                    inner_call_node = child_item.get("inner_call")
                    inner_callee_node = child_item.get("inner_callee")

                    if inner_call_node:
                        inner_callee = None
                        if inner_callee_node:
                            inner_callee = ScopeModel(
                                id=inner_callee_node["id"],
                                name=inner_callee_node["name"],
                                qname=inner_callee_node["qname"],
                                type=inner_callee_node["type"],
                                file_path=inner_callee_node["file_path"],
                                start_line=inner_callee_node["start_line"],
                                start_col=inner_callee_node["start_col"],
                                end_line=inner_callee_node["end_line"],
                                end_col=inner_callee_node["end_col"],
                                mro=inner_callee_node.get("mro", []),
                            )

                        children.append({
                            "call_site": CallSiteModel(
                                id=inner_call_node["id"],
                                line=inner_call_node["line"],
                                col=inner_call_node["col"],
                                name=inner_call_node.get("name"),
                            ),
                            "callee": inner_callee,
                        })
                call_info["children"] = children

            calls.append(call_info)
        return calls

    async def get_calls_from(self, caller_id: str) -> List[dict]:
        """Get all calls made from a scope (including unresolved callees)."""

        result = await self.db_manager.connection.execute(
            """
            MATCH (caller:Scope {id: $caller_id})-[:HAS_CALL_SITE]->(cs:CallSite)
            OPTIONAL MATCH (cs)-[:TARGETS]->(callee:Scope)
            RETURN cs, callee
            """,
            {"caller_id": caller_id}
        )

        calls = []
        for row in result:
            cs_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            calls.append({
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                    name=cs_node.get("name"),
                ),
                "callee": callee,
            })
        return calls

    async def get_call_chain_children(self, call_site_id: str) -> List[dict]:
        """Get NEXT_IN_CHAIN children for a call site, plus their target scope."""

        result = await self.db_manager.connection.execute(
            """
            MATCH (cs:CallSite {id: $call_site_id})-[:NEXT_IN_CHAIN]->(child:CallSite)
            OPTIONAL MATCH (child)-[:TARGETS]->(callee:Scope)
            RETURN child, callee
            """,
            {"call_site_id": call_site_id}
        )

        children = []
        for row in result:
            child_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            children.append({
                "call_site": CallSiteModel(
                    id=child_node["id"],
                    line=child_node["line"],
                    col=child_node["col"],
                    name=child_node.get("name"),
                ),
                "callee": callee,
            })
        return children

    async def get_calls_inside_callee(self, call_site_id: str) -> List[dict]:
        """
        Get calls made INSIDE the scope targeted by this call site.

        This follows the pattern:
        CallSite -[:TARGETS]-> Scope -[:HAS_CALL_SITE]-> CallSite

        Returns calls that are executed within the callee function's body.
        """

        result = await self.db_manager.connection.execute(
            """
            MATCH (cs:CallSite {id: $call_site_id})-[:TARGETS]->(callee:Scope)
            MATCH (callee)-[:HAS_CALL_SITE]->(inner_call:CallSite)
            OPTIONAL MATCH (inner_call)-[:TARGETS]->(inner_callee:Scope)
            RETURN inner_call, inner_callee
            """,
            {"call_site_id": call_site_id}
        )

        calls = []
        for row in result:
            call_node = row[0]
            callee_node = row[1] if len(row) > 1 else None

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            calls.append({
                "call_site": CallSiteModel(
                    id=call_node["id"],
                    line=call_node["line"],
                    col=call_node["col"],
                    name=call_node.get("name"),
                ),
                "callee": callee,
            })
        return calls

    async def batch_get_calls_inside_callee(
        self, call_site_ids: List[str]
    ) -> dict:
        """
        Batch fetch calls made INSIDE the scopes targeted by multiple call
        sites.

        Args:
            call_site_ids: List of call site IDs to fetch calls for

        Returns:
            Dictionary mapping call_site_id -> List[dict] of call infos
        """
        if not call_site_ids:
            return {}

        result = await self.db_manager.connection.execute(
            """
            UNWIND $call_site_ids AS call_site_id
            MATCH (cs:CallSite {id: call_site_id})-[:TARGETS]->(callee:Scope)
            MATCH (callee)-[:HAS_CALL_SITE]->(inner_call:CallSite)
            OPTIONAL MATCH (inner_call)-[:TARGETS]->(inner_callee:Scope)
            RETURN call_site_id, inner_call, inner_callee
            """,
            {"call_site_ids": call_site_ids}
        )

        calls_map = {}
        for row in result:
            call_site_id = row[0]
            call_node = row[1]
            callee_node = row[2] if len(row) > 2 else None

            if call_site_id not in calls_map:
                calls_map[call_site_id] = []

            callee = None
            if callee_node:
                callee = ScopeModel(
                    id=callee_node["id"],
                    name=callee_node["name"],
                    qname=callee_node["qname"],
                    type=callee_node["type"],
                    file_path=callee_node["file_path"],
                    start_line=callee_node["start_line"],
                    start_col=callee_node["start_col"],
                    end_line=callee_node["end_line"],
                    end_col=callee_node["end_col"],
                    mro=callee_node.get("mro", []),
                )

            calls_map[call_site_id].append({
                "call_site": CallSiteModel(
                    id=call_node["id"],
                    line=call_node["line"],
                    col=call_node["col"],
                    name=call_node.get("name"),
                ),
                "callee": callee,
            })

        # Ensure all call_site_ids have entries (even if empty)
        for call_site_id in call_site_ids:
            if call_site_id not in calls_map:
                calls_map[call_site_id] = []

        return calls_map

    async def get_calls_to(self, callee_id: str) -> List[dict]:
        """Get all calls made to a scope."""

        result = await self.db_manager.connection.execute(
            """
            MATCH (caller:Scope)-[:HAS_CALL_SITE]->(cs:CallSite)-[:TARGETS]->(callee:Scope {id: $callee_id})
            RETURN cs, caller
            """,
            {"callee_id": callee_id}
        )

        calls = []
        for row in result:
            cs_node = row[0]
            caller_node = row[1]
            calls.append({
                "call_site": CallSiteModel(
                    id=cs_node["id"],
                    line=cs_node["line"],
                    col=cs_node["col"],
                    name=cs_node.get("name"),
                ),
                "caller": ScopeModel(
                    id=caller_node["id"],
                    name=caller_node["name"],
                    qname=caller_node["qname"],
                    type=caller_node["type"],
                    file_path=caller_node["file_path"],
                    start_line=caller_node["start_line"],
                    start_col=caller_node["start_col"],
                    end_line=caller_node["end_line"],
                    end_col=caller_node["end_col"],
                    mro=caller_node.get("mro", []),
                ),
            })
        return calls

    async def get_call_chain(self, call_site_id: str) -> List[CallSiteModel]:
        """Get the full call chain starting from a call site."""
        return await self.repository.get_call_chain(call_site_id)

    async def get_call_chain_roots(self, target_scope_id: Optional[str] = None) -> List[CallSiteModel]:
        """
        Get all call sites that are roots of call chains.

        If `target_scope_id` is provided, only return those root call sites for which
        there exists a path along `NEXT_IN_CHAIN` that contains a call site targeting
        the given scope.
        """
        return await self.repository.get_call_chain_roots(target_scope_id)

    async def clear_calls(self, scope_id: str) -> None:
        """Clear all calls originating from a scope."""
        async with self.semaphore:
            await self.repository.clear_calls_from_scope(scope_id)

    async def batch_clear_calls(self, scope_ids: List[str]) -> None:
        """Batch clear all calls originating from multiple scopes."""
        async with self.semaphore:
            await self.repository.batch_clear_calls_from_scopes(scope_ids)

    # Utility

    async def clear_all(self) -> None:
        """Clear all data from the database."""
        async with self.semaphore:
            await self.repository.clear_db()

    async def delete_cache(self) -> None:
        """Delete the cache."""
        async with self.semaphore:
            self.db_manager.delete_db()
