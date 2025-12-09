from typing import List

from ..db import DBConnectionManager
from ..models import ScopeModel


class QueryRepository:
    """Repository for querying scopes."""

    def __init__(self, db_manager: DBConnectionManager):
        self.conn = db_manager.get_connection()

    def get_all_scopes(self) -> List[ScopeModel]:
        """Get all scopes."""
        result = self.conn.execute("MATCH (s:Scope) RETURN s")
        scopes = []
        for row in result:
            node = row[0]
            scopes.append(ScopeModel(
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
            ))
        return scopes

    def get_all_file_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FILE."""
        result = self.conn.execute("MATCH (s:Scope {type: 'file'}) RETURN s")
        scopes = []
        for row in result:
            node = row[0]
            scopes.append(ScopeModel(
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
            ))
        return scopes

    def get_all_folder_scopes(self) -> List[ScopeModel]:
        """Get all scopes of type FOLDER."""
        result = self.conn.execute("MATCH (s:Scope {type: 'folder'}) RETURN s")
        scopes = []
        for row in result:
            node = row[0]
            scopes.append(ScopeModel(
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
            ))
        return scopes

