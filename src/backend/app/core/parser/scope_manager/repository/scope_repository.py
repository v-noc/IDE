import gc
from typing import List, Optional

from ..db import DBConnectionManager
from ..models import ScopeModel


class ScopeRepository:
    """Repository for scope CRUD operations."""

    def __init__(self, db_manager: DBConnectionManager):
        self.db_manager = db_manager

    async def create_scope(self, scope: ScopeModel) -> None:
        """Create a Scope node."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                CREATE (s:Scope {
                    id: $id,
                    name: $name,
                    qname: $qname,
                    type: $type,
                    file_path: $file_path,
                    start_line: $start_line,
                    start_col: $start_col,
                    end_line: $end_line,
                    end_col: $end_col,
                    mro: $mro,
                    checksum: $checksum
                })
                """,
                {
                    "id": scope.id,
                    "name": scope.name,
                    "qname": scope.qname,
                    "type": scope.type.value,
                    "file_path": scope.file_path,
                    "start_line": scope.start_line,
                    "start_col": scope.start_col,
                    "end_line": scope.end_line,
                    "end_col": scope.end_col,
                    "mro": scope.mro,
                    "checksum": scope.checksum,
                },
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def update_scope(self, scope: ScopeModel) -> None:
        """Update an existing Scope node's properties."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                MATCH (s:Scope {id: $id})
                SET s.name = $name,
                    s.qname = $qname,
                    s.type = $type,
                    s.file_path = $file_path,
                    s.start_line = $start_line,
                    s.start_col = $start_col,
                    s.end_line = $end_line,
                    s.end_col = $end_col,
                    s.mro = $mro,
                    s.checksum = $checksum
                """,
                {
                    "id": scope.id,
                    "name": scope.name,
                    "qname": scope.qname,
                    "type": scope.type.value,
                    "file_path": scope.file_path,
                    "start_line": scope.start_line,
                    "start_col": scope.start_col,
                    "end_line": scope.end_line,
                    "end_col": scope.end_col,
                    "mro": scope.mro,
                    "checksum": scope.checksum,
                },
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_update_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch update multiple scopes efficiently using Neo4j UNWIND."""
        if not scopes:
            return

        scope_data = []
        for scope in scopes:
            scope_data.append({
                "id": scope.id,
                "name": scope.name,
                "qname": scope.qname,
                "type": scope.type.value,
                "file_path": scope.file_path,
                "start_line": scope.start_line,
                "start_col": scope.start_col,
                "end_line": scope.end_line,
                "end_col": scope.end_col,
                "mro": scope.mro or [],
                "checksum": scope.checksum,
            })

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $scopes AS scope_data
                MATCH (s:Scope {id: scope_data.id})
                SET s.name = scope_data.name,
                    s.qname = scope_data.qname,
                    s.type = scope_data.type,
                    s.file_path = scope_data.file_path,
                    s.start_line = scope_data.start_line,
                    s.start_col = scope_data.start_col,
                    s.end_line = scope_data.end_line,
                    s.end_col = scope_data.end_col,
                    s.mro = scope_data.mro,
                    s.checksum = scope_data.checksum
                """,
                {"scopes": scope_data},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_scope_by_id(self, scope_id: str) -> Optional[ScopeModel]:
        """Get a Scope by ID."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {id: $id}) RETURN s",
                {"id": scope_id},
            )

            for row in result:
                node = row[0]
                return ScopeModel(
                    id=node["id"],
                    name=node["name"],
                    qname=node["qname"],
                    type=node["type"],
                    file_path=node["file_path"],
                    start_line=node["start_line"],
                    start_col=node["start_col"],
                    end_line=node["end_line"],
                    end_col=node["end_col"],
                    mro=node.get("mro", []),
                    checksum=node.get("checksum"),
                )
            return None
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_scope_by_qname(self, qname: str) -> Optional[ScopeModel]:
        """Get a scope by its qualified name."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {qname: $qname}) RETURN s",
                {"qname": qname},
            )
            for row in result:
                node = row[0]
                return ScopeModel(
                    id=node["id"],
                    name=node["name"],
                    qname=node["qname"],
                    type=node["type"],
                    file_path=node["file_path"],
                    start_line=node["start_line"],
                    start_col=node["start_col"],
                    end_line=node["end_line"],
                    end_col=node["end_col"],
                    mro=node.get("mro", []),
                    checksum=node.get("checksum"),
                )
            return None
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_get_scopes_by_qnames(
        self, qnames: List[str]
    ) -> dict[str, ScopeModel]:
        """
        Batch get scopes by their qualified names.
        Returns a dict mapping qname -> ScopeModel.
        """
        if not qnames:
            return {}

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $qnames AS qname
                MATCH (s:Scope {qname: qname})
                RETURN s.qname AS qname, s
                """,
                {"qnames": qnames},
            )

            scopes_map = {}
            for row in result:
                qname = row[0]
                node = row[1]
                scopes_map[qname] = ScopeModel(
                    id=node["id"],
                    name=node["name"],
                    qname=node["qname"],
                    type=node["type"],
                    file_path=node["file_path"],
                    start_line=node["start_line"],
                    start_col=node["start_col"],
                    end_line=node["end_line"],
                    end_col=node["end_col"],
                    mro=node.get("mro", []),
                    checksum=node.get("checksum"),
                )
            return scopes_map
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_get_scopes_by_ids(
        self, scope_ids: List[str]
    ) -> dict[str, ScopeModel]:
        """
        Batch get scopes by their IDs.
        Returns a dict mapping id -> ScopeModel.
        """
        if not scope_ids:
            return {}

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $scope_ids AS scope_id
                MATCH (s:Scope {id: scope_id})
                RETURN s.id AS id, s
                """,
                {"scope_ids": scope_ids},
            )

            scopes_map = {}
            for row in result:
                scope_id = row[0]
                node = row[1]
                scopes_map[scope_id] = ScopeModel(
                    id=node["id"],
                    name=node["name"],
                    qname=node["qname"],
                    type=node["type"],
                    file_path=node["file_path"],
                    start_line=node["start_line"],
                    start_col=node["start_col"],
                    end_line=node["end_line"],
                    end_col=node["end_col"],
                    mro=node.get("mro", []),
                    checksum=node.get("checksum"),
                )
            return scopes_map
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def batch_create_scopes(self, scopes: List[ScopeModel]) -> None:
        """Batch create multiple scopes efficiently using Neo4j UNWIND."""
        if not scopes:
            return

        scope_data = []
        for scope in scopes:
            scope_data.append({
                "id": scope.id,
                "name": scope.name,
                "qname": scope.qname,
                "type": scope.type.value,
                "file_path": scope.file_path,
                "start_line": scope.start_line,
                "start_col": scope.start_col,
                "end_line": scope.end_line,
                "end_col": scope.end_col,
                "mro": scope.mro or [],
                "checksum": scope.checksum,
            })

        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                """
                UNWIND $scopes AS scope_data
                CREATE (s:Scope {
                    id: scope_data.id,
                    name: scope_data.name,
                    qname: scope_data.qname,
                    type: scope_data.type,
                    file_path: scope_data.file_path,
                    start_line: scope_data.start_line,
                    start_col: scope_data.start_col,
                    end_line: scope_data.end_line,
                    end_col: scope_data.end_col,
                    mro: scope_data.mro,
                    checksum: scope_data.checksum
                })
                """,
                {"scopes": scope_data},
            )
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object
