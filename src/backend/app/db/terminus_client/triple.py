"""Triple and graph operations for TerminusDB."""

import json
from typing import Optional

from app.db.woql_utils import _finish_response

from .models import GraphType


class TripleMixin:
    """Mixin for triple/graph operations."""

    async def get_triples(self, graph_type: GraphType) -> str:
        """Retrieves the contents of the specified graph as triples encoded in turtle."""
        self._check_connection()
        result = await self._session.get(
            self._triples_url(graph_type),
            headers=self._default_headers,
            auth=self._auth(),
        )
        return json.loads(_finish_response(result))

    async def update_triples(
        self, graph_type: GraphType, content: str, commit_msg: str
    ) -> None:
        """Updates the contents of the specified graph with triples in turtle format."""
        self._check_connection()
        params = {
            "commit_info": self._generate_commit(commit_msg),
            "turtle": content,
        }
        result = await self._session.post(
            self._triples_url(graph_type),
            headers=self._default_headers,
            json=params,
            auth=self._auth(),
        )
        json.loads(_finish_response(result))

    async def insert_triples(
        self, graph_type: GraphType, content: str, commit_msg: Optional[str] = None
    ) -> None:
        """Inserts into the specified graph with triples in turtle format."""
        self._check_connection()
        params = {
            "commit_info": self._generate_commit(commit_msg),
            "turtle": content,
        }
        result = await self._session.put(
            self._triples_url(graph_type),
            headers=self._default_headers,
            json=params,
            auth=self._auth(),
        )
        json.loads(_finish_response(result))
