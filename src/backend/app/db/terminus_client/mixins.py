import base64
import os
import urllib.parse as urlparse
from typing import Optional

import httpx
from terminusdb_client.__version__ import __version__

from .auth import APITokenAuth, JWTAuth
from .models import GraphType


class AsyncClientAuthMixin:
    def _generate_commit(
        self, msg: Optional[str] = None, author: Optional[str] = None
    ) -> dict:
        if author:
            mes_author = author
        else:
            mes_author = self._author
        if not msg:
            msg = f"Commit via python client {__version__}"
        return {"author": mes_author, "message": msg}

    def _auth(self) -> httpx.Auth:
        if not self._use_token and self._connected and self._key and self.user:
            return httpx.BasicAuth(self.user, self._key)
        elif self._connected and self._jwt_token is not None:
            return JWTAuth(self._jwt_token)
        elif self._connected and self._api_token is not None:
            return APITokenAuth(self._api_token)
        elif self._connected:
            return APITokenAuth(os.environ["TERMINUSDB_ACCESS_TOKEN"])
        else:
            raise RuntimeError("Client not connected.")

    def _remote_auth(self):
        if self._remote_auth_dict:
            return self._generate_remote_header(self._remote_auth_dict)
        elif "TERMINUSDB_REMOTE_ACCESS_TOKEN" in os.environ:
            token = os.environ["TERMINUSDB_REMOTE_ACCESS_TOKEN"]
            return f"Token {token}"

    def _generate_remote_header(self, remote_auth: dict):
        key_type = remote_auth["type"]
        key = remote_auth["key"]
        if key_type == "http_basic":
            username = remote_auth["username"]
            http_basic_creds = base64.b64encode(
                f"{username}:{key}".encode('utf-8')).decode('utf-8')
            return f"Basic {http_basic_creds}"
        elif key_type == "token":
            return f"Token {key}"
        return f"Bearer {key}"


class AsyncClientURLMixin:
    def _db_url_fragment(self):
        if self._db == "_system":
            return self._db
        return f"{self._team}/{self._db}"

    def _db_base(self, action: str):
        return f"{self.api}/{action}/{self._db_url_fragment()}"

    def _branch_url(self, branch_id: str):
        base_url = self._repo_base("branch")
        branch_id = urlparse.quote(branch_id)
        return f"{base_url}/branch/{branch_id}"

    def _repo_base(self, action: str):
        return self._db_base(action) + f"/{self._repo}"

    def _branch_base(self, action: str, branch: Optional[str] = None):
        base = self._repo_base(action)

        if self._repo == "_meta":
            return base
        if self._branch == "_commits":
            return base + f"/{self._branch}"
        elif self.ref:
            return base + f"/commit/{self._ref}"
        elif branch:
            return base + f"/branch/{branch}"
        else:
            return base + f"/branch/{self._branch}"

    def _query_url(self):
        if self._db == "_system":
            return self._db_base("woql")
        return self._branch_base("woql")

    def _class_frame_url(self):
        if self._db == "_system":
            return self._db_base("schema")
        return self._branch_base("schema")

    def _capabilities_url(self):
        return f"{self.api}/capabilities"

    def _organization_url(self):
        return f"{self.api}/organizations"

    def _users_url(self):
        return f"{self.api}/users"

    def _roles_url(self):
        return f"{self.api}/roles"

    def _documents_url(self, branch_name: Optional[str] = None):
        if self._db == "_system":
            base_url = self._db_base("document")
        else:
            base_url = self._branch_base("document", branch=branch_name)
        return base_url

    def _triples_url(self, graph_type: GraphType = GraphType.INSTANCE):
        if self._db == "_system":
            base_url = self._db_base("triples")
        else:
            base_url = self._branch_base("triples")
        return f"{base_url}/{graph_type}"

    def _clone_url(self, new_repo_id: str):
        new_repo_id = urlparse.quote(new_repo_id)
        return f"{self.api}/clone/{self._team}/{new_repo_id}"

    def _cloneable_url(self):
        return f"{self.server_url}/{self._team}/{self._db}"

    def _pull_url(self):
        return self._branch_base("pull")

    def _fetch_url(self, remote_name: str):
        furl = self._branch_base("fetch")
        remote_name = urlparse.quote(remote_name)
        return furl + "/" + remote_name + "/_commits"

    def _rebase_url(self):
        return self._branch_base("rebase")

    def _reset_url(self):
        return self._branch_base("reset")

    def _optimize_url(self, path: str):
        path = urlparse.quote(path)
        return f"{self.api}/optimize/{path}"

    def _squash_url(self, branch_name: Optional[str] = None):
        return self._branch_base("squash", branch=branch_name)

    def _diff_url(self):
        return self._branch_base("diff")

    def _apply_url(self, branch: Optional[str] = None):
        return self._branch_base("apply", branch)

    def _patch_url(self):
        return f"{self.api}/patch"

    def _push_url(self):
        return self._branch_base("push")

    def _db_url(self):
        return self._db_base("db")

    def _prefix_url(self, prefix_name: Optional[str] = None):
        base = self._db_base("prefix")
        if self._db == "_system":
            if prefix_name is None:
                return base
            return f"{base}/{urlparse.quote(prefix_name)}"
        base = self._branch_base("prefix")
        if prefix_name is None:
            return base
        return f"{base}/{urlparse.quote(prefix_name)}"
