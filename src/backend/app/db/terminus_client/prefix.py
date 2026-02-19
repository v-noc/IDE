"""Prefix management for TerminusDB."""


class PrefixMixin:
    """Mixin for prefix operations."""

    async def _get_prefixes(self):
        """Get the prefixes for a given database."""
        self._check_connection()
        result = await self._session.get(
            self._db_base("prefixes"),
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()

    async def get_prefix(self, prefix_name: str) -> str:
        """Get a single prefix IRI by name."""
        self._check_connection()
        result = await self._session.get(
            self._prefix_url(prefix_name),
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()["api:prefix_uri"]

    async def add_prefix(self, prefix_name: str, uri: str) -> dict:
        """Add a new prefix mapping."""
        self._check_connection()
        result = await self._session.post(
            self._prefix_url(prefix_name),
            json={"uri": uri},
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()

    async def update_prefix(self, prefix_name: str, uri: str) -> dict:
        """Update an existing prefix mapping."""
        self._check_connection()
        result = await self._session.put(
            self._prefix_url(prefix_name),
            json={"uri": uri},
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()

    async def upsert_prefix(self, prefix_name: str, uri: str) -> dict:
        """Create or update a prefix mapping (upsert)."""
        self._check_connection()
        result = await self._session.put(
            self._prefix_url(prefix_name) + "?create=true",
            json={"uri": uri},
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()

    async def delete_prefix(self, prefix_name: str) -> dict:
        """Delete a prefix mapping."""
        self._check_connection()
        result = await self._session.delete(
            self._prefix_url(prefix_name),
            headers=self._default_headers,
            auth=self._auth(),
        )
        result.raise_for_status()
        return result.json()
