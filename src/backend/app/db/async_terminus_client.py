"""Client.py
Client is the Python public API for TerminusDB"""

import json
import urllib.parse as urlparse
from typing import Optional

import httpx

from terminusdb_client.__version__ import __version__
from terminusdb_client.errors import InterfaceError
from .errors import DatabaseError
from .terminus_client.admin import AdminMixin
from .terminus_client.branch import BranchMixin
from .terminus_client.database import DatabaseMixin
from .terminus_client.diff import DiffMixin
from .terminus_client.document import DocumentMixin
from .terminus_client.mixins import AsyncClientAuthMixin, AsyncClientURLMixin
from .terminus_client.models import GraphType, Patch, WoqlResult
from .terminus_client.prefix import PrefixMixin
from .terminus_client.remote import RemoteMixin
from .terminus_client.triple import TripleMixin
from .woql_utils import _clean_dict, _dt_dict, _dt_list, _finish_response

# Re-export for backward compatibility
from terminusdb_client.woqlquery.woql_query import WOQLQuery

# client object
# license Apache Version 2
# summary Python module for accessing the Terminus DB API


class AsyncClient(
    AdminMixin,
    DiffMixin,
    RemoteMixin,
    BranchMixin,
    DocumentMixin,
    TripleMixin,
    PrefixMixin,
    DatabaseMixin,
    AsyncClientURLMixin,
    AsyncClientAuthMixin,
):
    """Client for TerminusDB server.

    Attributes
    ----------
    server_url : str
        URL of the server that this client connected.
    api : str
        API endpoint for this client.
    team : str
        Team that this client is using. "admin" for local dbs.
    db : str
        Database that this client is connected to.
    user : str
        TerminiusDB user that this client is using. "admin" for local dbs.
    branch : str
        Branch of the database that this client is connected to. Default to "main".
    ref : str, None
        Ref setting for the client. Default to None.
    repo : str
        Repo identifier of the database that this client is connected to. Default to "local".
    """

    def from_json(self, json_str):
        content = json.loads(json_str)
        if isinstance(content, dict):
            self.content = _dt_dict(content)
        else:
            self.content = _dt_list(content)

    def to_json(self):
        return json.dumps(_clean_dict(self.content))

    def __init__(
        self,
        server_url: str,
        user_agent: str = f"terminusdb-client-python/{__version__}",
        **kwargs,
    ) -> None:
        r"""The Client constructor.

        Parameters
        ----------
        server_url : str
            URL of the server that this client will connect to.
        user_agent : optional, str
            User agent header when making requests. Defaults to terminusdb-client-python with the version appended.
        **kwargs
            Extra configuration options

        """
        self.server_url = server_url.strip("/")
        self.api = f"{self.server_url}/api"
        self._connected = False

        # properties with get/setters
        self._team = None
        self._db = None
        self._user = None
        self._branch = None
        self._ref = None
        self._repo = None
        self._references = {}

        # Default headers
        self._default_headers = {"user-agent": user_agent}

    @property
    def team(self):
        if isinstance(self._team, str):
            return urlparse.unquote(self._team)
        else:
            return self._team

    @team.setter
    def team(self, value):
        if isinstance(value, str):
            self._team = urlparse.quote(value)
        else:
            self._team = value

    @property
    def db(self):
        if isinstance(self._db, str):
            return urlparse.unquote(self._db)
        else:
            return self._db

    @db.setter
    def db(self, value):
        if isinstance(value, str):
            self._db = urlparse.quote(value)
        else:
            self._db = value

    @property
    def user(self):
        if isinstance(self._user, str):
            return urlparse.unquote(self._user)
        else:
            return self._user

    @user.setter
    def user(self, value):
        if isinstance(value, str):
            self._user = urlparse.quote(value)
        else:
            self._user = value

    @property
    def branch(self):
        if isinstance(self._branch, str):
            return urlparse.unquote(self._branch)
        else:
            return self._branch

    @branch.setter
    def branch(self, value):
        if isinstance(value, str):
            self._branch = urlparse.quote(value)
        else:
            self._branch = value

    @property
    def repo(self):
        if isinstance(self._repo, str):
            return urlparse.unquote(self._repo)
        else:
            self._repo

    @repo.setter
    def repo(self, value):
        if isinstance(value, str):
            self._repo = urlparse.quote(value)
        else:
            self._repo = value

    @property
    def ref(self):
        return self._ref

    @ref.setter
    def ref(self, value: Optional[str]):
        if value is not None:
            value = value.lower()
        self._ref = value

    async def connect(
        self,
        team: str = "admin",
        db: Optional[str] = None,
        remote_auth: Optional[dict] = None,
        use_token: bool = False,
        jwt_token: Optional[str] = None,
        api_token: Optional[str] = None,
        key: str = "root",
        user: str = "admin",
        branch: str = "main",
        ref: Optional[str] = None,
        repo: str = "local",
        **kwargs,
    ) -> None:
        r"""Connect to a Terminus server at the given URI with an API key.

        Stores the connection settings and necessary meta-data for the connected server. You need to connect before most database operations.

        Parameters
        ----------
        team : str
            Name of the team, default to be "admin"
        db : optional, str
            Name of the database connected
        remote_auth : optional, dict
            Remote Auth setting
        key : optional, str
            API key for connecting, default to be "root"
        user : optional, str
            Name of the user, default to be "admin"
        use_token : bool
            Use token to connect. If both `jwt_token` and `api_token` is not provided (None), then it will use the ENV variable TERMINUSDB_ACCESS_TOKEN to connect as the API token
        jwt_token : optional, str
            The Bearer JWT token to connect. Default to be None.
        api_token : optional, strs
            The API token to connect. Default to be None.
        branch : optional, str
            Branch to be connected, default to be "main"
        ref : optional, str
            Ref setting
        repo : optional, str
            Local or remote repo, default to be "local"
        **kwargs
            Extra configuration options.

        Examples
        --------
        >>> client = Client("http://127.0.0.1:6363")
        >>> client.connect(key="root", team="admin", user="admin", db="example_db")
        """

        self.team = team
        self.db = db
        self._remote_auth_dict = remote_auth
        self._key = key
        self.user = user
        if api_token:
            self._use_token = True
        else:
            self._use_token = use_token
        self._jwt_token = jwt_token
        self._api_token = api_token
        self.branch = branch
        self.ref = ref
        self.repo = repo
        self._session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=30),

        )
        self._connected = True

        try:
            self._db_info = await self.info()
        except Exception as error:
            raise InterfaceError(
                f"Cannot connect to server, please make sure TerminusDB is running at {self.server_url} and the authentication details are correct. Details: {str(error)}"
            ) from None
        if self.db is not None:
            try:
                _finish_response(
                    await self._session.head(
                        self._db_url(),
                        headers=self._default_headers,
                        params={"exists": "true"},
                        auth=self._auth(),
                    )
                )
            except DatabaseError:
                raise InterfaceError(
                    f"Connection fail, {self.db} does not exist.")
        self._author = self.user

    async def close(self) -> None:
        """Undo connect and close the connection.

        The connection will be unusable from this point forward; an Error (or subclass) exception will be raised if any operation is attempted with the connection, unless connect is call again.
        """
        if self._session is not None:
            await self._session.aclose()
        self._connected = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _check_connection(self, check_db=True) -> None:
        """Raise connection InterfaceError if not connected
        Defaults to check if a db is connected"""
        if not self._connected:
            raise InterfaceError(
                "Client is not connected to a TerminusDB server.")
        if check_db and self.db is None:
            raise InterfaceError(
                "No database is connected. Please either connect to a database or create a new database."
            )

    async def info(self) -> dict:
        """Get info of a TerminusDB database server

        Returns
        -------
        dict

             Dict with version information:
             ```
             {
               "@type": "api:InfoResponse",
               "api:info": {
                 "authority": "anonymous",
                 "storage": {
                   "version": "1"
                 },
                 "terminusdb": {
                   "git_hash": "53acb38f9aedeec6c524f5679965488788e6ccf5",
                   "version": "10.1.5"
                 },
                 "terminusdb_store": {
                   "version": "0.19.8"
                 }
               },
               "api:status": "api:success"
             }
             ```
        """
        return json.loads(
            _finish_response(
                await self._session.get(
                    self.api + "/info",
                    headers=self._default_headers,
                    auth=self._auth(),
                )
            )
        )

    async def ok(self) -> bool:
        """Check whether the TerminusDB server is still OK.
           Status is not OK when this function returns false
           or throws an exception (mostly ConnectTimeout)

        Raises
        ------
        Exception
            When a connection can't be made by the requests library

        Returns
        -------
        bool
        """
        if not self._connected:
            return self._connected
        req = await self._session.get(
            self.api + "/ok", headers=self._default_headers, timeout=6
        )
        return req.status_code == 200

    def clone(self, **overrides) -> "AsyncClient":
        """Create a shallow client clone that shares session/auth state."""
        server_url = overrides.pop("server_url", self.server_url)
        user_agent = overrides.pop(
            "user_agent",
            self._default_headers.get(
                "user-agent", f"terminusdb-client-python/{__version__}"),
        )
        session = overrides.pop("session", getattr(self, "_session", None))

        cloned = AsyncClient(server_url=server_url, user_agent=user_agent)

        cloned.team = overrides.pop("team", self.team)

        cloned.db = overrides.pop("db", self.db)
        cloned.user = overrides.pop("user", self.user)
        cloned.branch = overrides.pop("branch", self.branch)
        cloned.ref = overrides.pop("ref", self.ref)
        cloned.repo = overrides.pop("repo", self.repo)

        cloned._connected = overrides.pop("connected", self._connected)
        cloned._references = {}
        cloned._default_headers = self._default_headers.copy()
        if session is not None:
            cloned._session = session

        # Keep auth/context metadata shared with the current connection.
        for attr in (
            "_remote_auth_dict",
            "_key",
            "_use_token",
            "_jwt_token",
            "_api_token",
            "_author",
            "_db_info",
        ):
            if attr in overrides:
                setattr(cloned, attr, overrides.pop(attr))
            elif hasattr(self, attr):
                setattr(cloned, attr, getattr(self, attr))

        if overrides:
            unknown = ", ".join(sorted(overrides.keys()))
            raise ValueError(f"Unknown clone override keys: {unknown}")

        return cloned

    def copy(self) -> "AsyncClient":
        """Create a shallow copy of this client."""
        return self.clone()


# Re-export for backward compatibility
__all__ = ["AsyncClient", "GraphType", "Patch", "WoqlResult", "WOQLQuery"]
