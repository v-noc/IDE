"""Branch and commit history operations for TerminusDB."""

import json
from datetime import datetime
from typing import Optional

from app.db.woql_utils import _finish_response, _result2stream


class BranchMixin:
    """Mixin for branch and commit history operations."""

    async def log(
        self,
        team: Optional[str] = None,
        db: Optional[str] = None,
        start: int = 0,
        count: int = -1,
        branch_name: Optional[str] = None,
    ):
        """Get commit history of a database."""
        self._check_connection(check_db=(not team or not db))
        team = team if team else self.team
        db = db if db else self.db
        result = await self._session.get(
            f"{self.api}/log/{team}/{db}",
            params={"start": start, "count": count},
            headers=self._default_headers,
            auth=self._auth(),
        )
        commits = json.loads(_finish_response(result))
        for commit in commits:
            commit["timestamp"] = datetime.fromtimestamp(commit["timestamp"])
            commit["commit"] = commit["identifier"]  # For backwards compat.
        return commits

    async def get_commit_history(
        self, max_history: int = 500, branch_name: Optional[str] = None
    ) -> list:
        """Get the whole commit history."""
        if max_history < 0:
            raise ValueError("max_history needs to be non-negative.")
        return await self.log(count=max_history, branch_name=branch_name)

    async def get_document_history(
        self,
        doc_id: str,
        team: Optional[str] = None,
        db: Optional[str] = None,
        start: int = 0,
        count: int = 10,
        created: bool = False,
        updated: bool = False,
    ) -> list:
        """Get the commit history for a specific document."""
        self._check_connection(check_db=(not team or not db))
        team = team if team else self.team
        db = db if db else self.db

        params = {
            "id": doc_id,
            "start": start,
            "count": count,
        }
        if created:
            params["created"] = created
        if updated:
            params["updated"] = updated

        result = await self._session.get(
            f"{self.api}/history/{team}/{db}",
            params=params,
            headers=self._default_headers,
            auth=self._auth(),
        )

        history = json.loads(_finish_response(result))

        if isinstance(history, list):
            for entry in history:
                if "timestamp" in entry and isinstance(
                    entry["timestamp"], (int, float)
                ):
                    entry["timestamp"] = datetime.fromtimestamp(
                        entry["timestamp"]
                    )

        return history

    async def _get_current_commit(self):
        descriptor = self.db
        if self.branch:
            descriptor = f"{descriptor}/local/branch/{self.branch}"
        commit = await self.log(team=self.team, db=descriptor, count=1)[0]
        return commit["identifier"]

    async def _get_target_commit(self, step):
        descriptor = self.db
        if self.branch:
            descriptor = f"{descriptor}/local/branch/{self.branch}"
        commit = await self.log(
            team=self.team, db=descriptor, count=1, start=step
        )[0]
        return commit["identifier"]

    async def get_all_branches(self, get_data_version=False):
        """Get all the branches available in the database."""
        self._check_connection()
        api_url = self._documents_url().split("/")
        api_url = api_url[:-2]
        api_url = "/".join(api_url) + "/_commits"
        result = await self._session.get(
            api_url,
            headers=self._default_headers,
            params={"type": "Branch"},
            auth=self._auth(),
        )

        if get_data_version:
            result, version = _finish_response(result, get_data_version)
            return list(_result2stream(result)), version

        return list(_result2stream(_finish_response(result)))

    def rollback(self, steps=1) -> None:
        """Not implemented: open transactions not supported."""
        raise NotImplementedError(
            "Open transactions are currently not supported. "
            "To reset commit head, check Client.reset"
        )

    async def create_branch(self, new_branch_id: str, empty: bool = False) -> None:
        """Create a branch starting from the current branch."""
        self._check_connection()
        if empty:
            source = {}
        elif self.ref:
            source = {
                "origin": f"{self.team}/{self.db}/{self.repo}/commit/{self.ref}"
            }
        else:
            source = {
                "origin": f"{self.team}/{self.db}/{self.repo}/branch/{self.branch}"
            }

        _finish_response(
            await self._session.post(
                self._branch_url(new_branch_id),
                headers=self._default_headers,
                json=source,
                auth=self._auth(),
            )
        )

    async def delete_branch(self, branch_id: str) -> None:
        """Delete a branch."""
        self._check_connection()

        _finish_response(
            await self._session.delete(
                self._branch_url(branch_id),
                headers=self._default_headers,
                auth=self._auth(),
            )
        )

    async def get_document_history(self,
                                   doc_id: str,
                                   team: Optional[str] = None,
                                   db: Optional[str] = None,
                                   start: int = 0,
                                   count: int = -1,
                                   created: bool = False,
                                   updated: bool = False):
        """Get commit history for a SPECIFIC document (uses the /history endpoint)

        This is the official, fast, server-side implementation of:
            terminusdb history admin/myDB/branch/main --id "Person/john"

        It only returns commits that actually touched the document (added, updated, or deleted it).
        Much faster and more efficient than looping over /log yourself.

        Parameters
        ----------
        doc_id : str
            The full document @id (e.g. "Person/john")
        team : str, optional
            Defaults to self.team
        db : str, optional
            Defaults to self.db
        start : int, optional
            Pagination start index (newest first). Default 0.
        count : int, optional
            Number of commits to return. Default -1 = all.
        created : bool, optional
            Return ONLY the commit where the document was created
        updated : bool, optional
            Return ONLY the commit where the document was last updated

        Returns
        -------
        list
            List of commit dictionaries (exactly like the log() method):
            [
              {
                "author": "admin",
                "identifier": "prh0yvftqmsrgctn8gqvdxv7gc4i8p8",
                "message": "Updated John's address",
                "timestamp": datetime.datetime(2024, ...),
                "commit": "prh0yvftqmsrgctn8gqvdxv7gc4i8p8"   # alias for backwards compatibility
              },
              ...
            ]
        """
        self._check_connection(check_db=(not team or not db))

        team = team if team else self.team
        db = db if db else self.db

        params = {
            'id': doc_id,
            'start': start,
            'count': count
        }
        if created:
            params['created'] = 'true'
        if updated:
            params['updated'] = 'true'

        result = await self._session.get(
            f"{self.api}/history/{team}/{db}",
            params=params,
            headers=self._default_headers,
            auth=self._auth(),
        )

        commits = json.loads(_finish_response(result))

        # Post-process exactly like your log() method
        for commit in commits:
            if isinstance(commit.get('timestamp'), (int, float)):
                commit['timestamp'] = datetime.fromtimestamp(
                    commit['timestamp'])
            commit['commit'] = commit.get(
                'identifier')  # backwards compatibility

        return commits
