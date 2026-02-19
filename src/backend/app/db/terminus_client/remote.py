"""Remote operations: push, pull, fetch, rebase, reset, optimize, squash."""

import json
from typing import Optional

from terminusdb_client.__version__ import __version__

from app.db.woql_utils import _finish_response


class RemoteMixin:
    """Mixin for remote repository operations."""

    async def pull(
        self,
        remote: str = "origin",
        remote_branch: Optional[str] = None,
        message: Optional[str] = None,
        author: Optional[str] = None,
    ) -> dict:
        """Pull updates from a remote repository to the current database."""
        self._check_connection()
        if remote_branch is None:
            remote_branch = self.branch
        if author is None:
            author = self._author
        if message is None:
            message = (
                f"Pulling from {remote}/{remote_branch} by Python client "
                f"{__version__}"
            )
        rc_args = {
            "remote": remote,
            "remote_branch": remote_branch,
            "author": author,
            "message": message,
        }

        result = await self._session.post(
            self._pull_url(),
            headers=self._default_headers,
            json=rc_args,
            auth=self._auth(),
        )

        return json.loads(_finish_response(result))

    async def fetch(
        self,
        remote_id: str,
        remote_auth: Optional[dict] = None,
    ) -> dict:
        """Fetch the branch from a remote repo."""
        self._check_connection()

        result = await self._session.post(
            self._fetch_url(remote_id),
            headers=self._default_headers,
            auth=self._auth(),
        )

        return json.loads(_finish_response(result))

    async def push(
        self,
        remote: str = "origin",
        remote_branch: Optional[str] = None,
        message: Optional[str] = None,
        author: Optional[str] = None,
        remote_auth: Optional[dict] = None,
    ) -> dict:
        """Push changes from a branch to a remote repo."""
        self._check_connection()
        if remote_branch is None:
            remote_branch = self.branch
        if author is None:
            author = self._author
        if message is None:
            message = (
                f"Pushing to {remote}/{remote_branch} by Python client "
                f"{__version__}"
            )
        rc_args = {
            "remote": remote,
            "remote_branch": remote_branch,
            "author": author,
            "message": message,
        }
        headers = self._default_headers.copy()
        if self._remote_auth_dict or remote_auth:
            headers["Authorization-Remote"] = (
                self._generate_remote_header(remote_auth)
                if remote_auth
                else self._remote_auth()
            )

        result = await self._session.post(
            self._push_url(),
            headers=headers,
            json=rc_args,
            auth=self._auth(),
        )

        return json.loads(_finish_response(result))

    async def rebase(
        self,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        rebase_source: Optional[str] = None,
        message: Optional[str] = None,
        author: Optional[str] = None,
        branch_name: Optional[str] = None,
    ) -> dict:
        """Rebase the current branch onto the specified remote branch."""
        self._check_connection()

        if branch is not None and commit is None:
            rebase_source = "/".join(
                [self.team, self.db, self.repo, "branch", branch]
            )
        elif branch is None and commit is not None:
            rebase_source = "/".join(
                [self.team, self.db, self.repo, "commit", commit]
            )
        elif branch is not None or commit is not None:
            raise RuntimeError("Cannot specify both branch and commit.")
        elif rebase_source is None:
            raise RuntimeError(
                "Need to specify one of 'branch', 'commit' or the 'rebase_source'"
            )

        if author is None:
            author = self._author
        if message is None:
            message = (
                f"Rebase from {rebase_source} by Python client {__version__}"
            )
        rc_args = {
            "rebase_from": rebase_source,
            "author": author,
            "message": message,
        }

        result = await self._session.post(
            self._rebase_url(),
            headers=self._default_headers,
            json=rc_args,
            auth=self._auth(),
        )

        return json.loads(_finish_response(result))

    async def reset(
        self,
        commit: Optional[str] = None,
        soft: bool = False,
        use_path: bool = False,
    ) -> None:
        """Reset the current branch HEAD to the specified commit."""
        self._check_connection()
        if soft:
            if use_path:
                self._ref = commit.split("/")[-1]
            else:
                self._ref = commit
            return None
        else:
            self._ref = None

        if commit is None:
            return None

        if use_path:
            commit_path = commit
        else:
            commit_path = f"{self.team}/{self.db}/{self.repo}/commit/{commit}"

        _finish_response(
            await self._session.post(
                self._reset_url(),
                headers=self._default_headers,
                json={"commit_descriptor": commit_path},
                auth=self._auth(),
            )
        )

    async def optimize(self, path: str) -> None:
        """Optimize the specified path."""
        self._check_connection()

        _finish_response(
            await self._session.post(
                self._optimize_url(path),
                headers=self._default_headers,
                auth=self._auth(),
            )
        )

    async def squash(
        self,
        message: Optional[str] = None,
        author: Optional[str] = None,
        reset: bool = False,
        branch_name: Optional[str] = None,
    ) -> str:
        """Squash the current branch HEAD into a commit."""
        self._check_connection()

        result = await self._session.post(
            self._squash_url(branch_name=branch_name),
            headers=self._default_headers,
            json={"commit_info": self._generate_commit(message, author)},
            auth=self._auth(),
        )

        commit_id = json.loads(_finish_response(result)).get("api:commit")
        if reset:
            await self.reset(commit_id)
        return commit_id
