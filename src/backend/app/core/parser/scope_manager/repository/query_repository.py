import gc
from typing import List

from ..db import DBConnectionManager
from ..models import ScopeModel


class QueryRepository:
    """Repository for querying scopes."""

    def __init__(self, db_manager: DBConnectionManager):
        self.db_manager = db_manager

    async def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute("MATCH (s:Scope) RETURN s")
            scopes = []
            for row in result:
                node = row[0]
                scopes.append(
                    ScopeModel(
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
                )
            return scopes
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {type: 'file'}) RETURN s"
            )
            scopes = []
            for row in result:
                node = row[0]
                scopes.append(
                    ScopeModel(
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
                )
            return scopes
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_all_folder_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FOLDER."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {type: 'folder'}) RETURN s"
            )
            scopes = []
            for row in result:
                node = row[0]
                scopes.append(
                    ScopeModel(
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
                )
            return scopes
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object

    async def get_scopes_by_file_path(self, file_path: str) -> List[ScopeModel]:
        """Get scopes by file path."""
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {file_path: $file_path}) RETURN s",
                {"file_path": file_path}
            )
            scopes = []
            for row in result:
                node = row[0]
                scopes.append(
                    ScopeModel(
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
                )
            return scopes
        finally:
            if result is not None:
                del result
                gc.collect()
        conn = self.db_manager.get_connection()
        result = None
        try:
            result = await conn.execute(
                "MATCH (s:Scope {type: 'folder'}) RETURN s"
            )
            scopes = []
            for row in result:
                node = row[0]
                scopes.append(
                    ScopeModel(
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
                )
            return scopes
        finally:
            if result is not None:
                del result
                gc.collect()  # Force immediate cleanup of the C++ object
