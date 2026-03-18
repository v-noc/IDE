import json
import httpx
from typing import Optional


class VectorLinkClient:
    """Async HTTP client for the VectorLink semantic indexer."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "VECTORLINK_EMBEDDING_API_KEY": 'openai secreate',
        }
        self._client = httpx.AsyncClient(
            base_url=base_url, headers=self.headers, timeout=30.0)

    async def index_document(
        self,
        db: str,
        commit_id: str,
        branch: str = "main",
    ) -> str:
        """Trigger vectorlink to start indexing and return the task id."""

        try:
            response = await self._client.get(
                f"/api/index",
                params={"domain": f"admin/{db}",
                        "commit": commit_id},
            )
            task_id = response.text
            return task_id
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Failed to index document: {e}") from e

    async def search(
        self,
        db: str,
        commit_id: str,
        query: str,
        branch: str = "main",
    ) -> list[dict]:
        """Search the vectorlink index and return the results."""

        try:
            response = await self._client.post(
                f"/api/search",
                params={"domain": f"admin/{db}",
                        "commit": commit_id},
                json={"search": query},
            )
            if response.status_code != 200:
                raise RuntimeError(f"Failed to search: {response.text}")

            return json.loads(response.text)
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Failed to search: {e}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse search response: {e}") from e
