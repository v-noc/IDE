"""Database management: create, delete, list, set, clone."""

import json
import warnings
from typing import Any, Dict, List, Optional

from app.db.woql_utils import _finish_response


class DatabaseMixin:
    """Mixin for database lifecycle operations."""

    async def create_database(
        self,
        dbid: str,
        team: Optional[str] = None,
        label: Optional[str] = None,
        description: Optional[str] = None,
        prefixes: Optional[dict] = None,
        include_schema: bool = True,
    ) -> None:
        """Create a TerminusDB database by posting a terminus:Database document."""
        self._check_connection(check_db=False)

        details: Dict[str, Any] = {}
        if label:
            details["label"] = label
        else:
            details["label"] = dbid
        if description:
            details["comment"] = description
        else:
            details["comment"] = ""
        if include_schema:
            details["schema"] = True
        else:
            details["schema"] = False
        if prefixes:
            details["prefixes"] = prefixes
        if team is None:
            team = self.team

        self.team = team
        self._connected = True
        self.db = dbid

        _finish_response(
            await self._session.post(
                self._db_url(),
                headers=self._default_headers,
                json=details,
                auth=self._auth(),
            )
        )

    async def delete_database(
        self,
        dbid: Optional[str] = None,
        team: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Delete a TerminusDB database."""
        self._check_connection(check_db=False)

        if dbid is None:
            raise UserWarning(
                f"You are currently using the database: {self.team}/{self.db}. "
                f"If you want to delete it, please do "
                f"'delete_database({self.db},{self.team})' instead."
            )

        self.db = dbid
        if team is None:
            warnings.warn(
                f"Delete Database Warning: You have not specify the team, "
                f"assuming {self.team}/{self.db}",
                stacklevel=2,
            )
        else:
            self.team = team
        payload = {}
        if force:
            payload["force"] = "true"
        _finish_response(
            await self._session.delete(
                self._db_url(),
                headers=self._default_headers,
                auth=self._auth(),
                params=payload,
            )
        )
        self.db = None

    async def set_db(self, dbid: str, team: Optional[str] = None) -> str:
        """Set the connection to another database."""
        self._check_connection(check_db=False)

        if team is None:
            team = self.team

        return await self.connect(
            team=team,
            db=dbid,
            remote_auth=self._remote_auth_dict,
            key=self._key,
            user=self.user,
            branch=self.branch,
            ref=self.ref,
            repo=self.repo,
        )

    async def get_database(
        self, dbid: str, team: Optional[str] = None
    ) -> Optional[dict]:
        """Returns metadata about the requested database."""
        self._check_connection(check_db=False)
        team = team if team else self.team
        result = await self._session.get(
            f"{self.api}/db/{team}/{dbid}?verbose=true",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def has_database(self, dbid: str, team: Optional[str] = None) -> bool:
        """Check whether a database exists."""
        self._check_connection(check_db=False)
        team = team if team else self.team
        r = await self._session.head(
            f"{self.api}/db/{team}/{dbid}",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return r.status_code == 200

    async def get_databases(self) -> List[dict]:
        """Returns a list of database metadata for all databases the user can access."""
        self._check_connection(check_db=False)
        result = await self._session.get(
            self.api + "/",
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def list_databases(self) -> List[Dict]:
        """Returns a list of database ids for all databases the user has access to."""
        self._check_connection(check_db=False)
        all_dbs = []
        for data in await self.get_databases():
            all_dbs.append(data["name"])
        return all_dbs

    async def clonedb(
        self,
        clone_source: str,
        newid: str,
        description: Optional[str] = None,
        remote_auth: Optional[dict] = None,
    ) -> None:
        """Clone a remote repository and create a local copy."""
        self._check_connection(check_db=False)
        if description is None:
            description = f"New database {newid}"

        headers = self._default_headers.copy()
        if self._remote_auth_dict or remote_auth:
            headers["Authorization-Remote"] = (
                self._generate_remote_header(remote_auth)
                if remote_auth
                else self._remote_auth()
            )

        rc_args = {
            "remote_url": clone_source,
            "label": newid,
            "comment": description,
        }

        _finish_response(
            await self._session.post(
                self._clone_url(newid),
                headers=headers,
                json=rc_args,
                auth=self._auth(),
            )
        )
