# app/db/repositories.py
from typing import (
    TypeVar,
    Generic,
    Type,
    List,
    Optional,
    Dict,
    Any,
    Union,
    get_origin,
)
from pydantic import BaseModel, TypeAdapter
from arangoasync.database import AsyncDatabase
from arangoasync.collection import StandardCollection
from arangoasync.exceptions import DocumentGetError
from datetime import datetime, timezone

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common functionality."""

    def __init__(
        self,
        db: AsyncDatabase,
        collection_name: str,
        model: Union[Type[T], TypeAdapter[T]],
        is_edge: bool = False,
        indexes: Optional[List[Dict[str, Any]]] = None,
        key_options: Optional[Dict[str, Any]] = None,
    ):
        self.db = db
        self.collection_name = collection_name
        self.model = model
        self.is_edge = is_edge
        config: Dict[str, Any] = getattr(model, "model_config", {}) or {}
        self.indexes = (
            indexes
            if indexes is not None
            else config.get("indexes") or []
        )
        self._collection: Optional[StandardCollection] = None
        # Configure ArangoDB key generation options. Default to UUID keys while
        # still allowing user-provided keys.
        self.key_options: Dict[str, Any] = (
            key_options
            or config.get("arango_key_options")
            or {

                "key_generator": "uuid",
                "user_keys": True,

            }
        )
        # Handle discriminated unions
        if get_origin(model) is Union or hasattr(model, "__metadata__"):
            self.adapter = TypeAdapter(model)
        else:
            self.adapter = None

    async def get_collection(self) -> StandardCollection:
        """Lazy-load collection handle asynchronously."""
        if self._collection is None:
            self._collection = await self._ensure_collection()
        return self._collection

    def _validate(self, doc: Dict[str, Any]) -> T:
        if self.adapter:
            return self.adapter.validate_python(doc)
        return self.model.model_validate(doc)

    async def _ensure_collection(self) -> StandardCollection:
        has_collection = await self.db.has_collection(self.collection_name)
        if has_collection:
            collection = await self.db.collection(self.collection_name)
            is_existing_edge = bool(collection.properties().get("edge", False))

            # CRITICAL: Check for type mismatch and
            # fail loudly instead of deleting
            if is_existing_edge != self.is_edge:
                expected_type = "edge" if self.is_edge else "document"
                raise TypeError(
                    (
                        "Collection '"
                        f"{self.collection_name}"
                        "' exists but has the wrong type. "
                        f"Expected a '{expected_type}' collection."
                    )
                )
        else:
            collection = await self.db.create_collection(
                self.collection_name,
                edge=self.is_edge,
                **self.key_options,  # This unpacks the dict
            )

        # Apply indexes
        for index_spec in self.indexes:
            try:
                await collection.add_hash_index(
                    fields=index_spec["fields"],
                    unique=index_spec.get("unique", False),
                )
            except Exception as e:
                # Prefer a specific python-arango exception and log it.
                # We'll check if it's an "already exists" error.
                if "duplicate name" not in str(e):
                    # Re-raise exceptions that are not about existing indexes
                    raise e

        return collection

    async def get_by_key(self, key: str) -> Optional[T]:
        try:
            collection = await self.get_collection()
            doc = await collection.get(key)
            return self._validate(doc) if doc else None
        except DocumentGetError:
            return None

    async def get_raw_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by its key without Pydantic validation."""
        collection = await self.get_collection()
        return await collection.get(key)

    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get by full document ID (collection/key)."""
        key = doc_id.split("/")[-1] if "/" in doc_id else doc_id
        return await self.get_by_key(key)

    async def create(self, entity: T, sync: bool = False) -> T:
        """Create a document and return the newly created version."""
        dump = entity.model_dump(by_alias=True, exclude_none=True, mode="json")
        # Get the full created document back in one call
        collection = await self.get_collection()
        meta = await collection.insert(
            dump,
            return_new=True,
            overwrite=True,
            sync=True
        )
        return self._validate(meta["new"])

    async def update(self, key: str, entity: T) -> T:
        """Update a document and return the newly updated version."""
        dump = entity.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude={"id", "key"},
            mode="json",
        )
        # Ensure updated_at reflects the time of update in UTC ISO8601
        dump["updated_at"] = (
            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        # python-arango expects a document payload containing _id or _key,
        # not a separate key argument. Provide the key inline with the
        # update body.
        document = {
            "_key": key,
            **dump,
        }
        collection = await self.get_collection()
        meta = await collection.update(
            document,
            return_new=True,

        )
        return self._validate(meta["new"])

    async def delete(self, key: str) -> bool:
        try:
            collection = await self.get_collection()
            await collection.delete(key)
            return True
        except DocumentGetError:
            return False

    async def find(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[T]:
        collection = await self.get_collection()
        cursor = await collection.find(
            filters,
            limit=limit,
        )
        results = []
        async for doc in cursor:
            results.append(self._validate(doc))

        return results

    async def find_stream(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        batch_size: int = 1000
    ):
        """
        Stream documents as async generator (memory-efficient).

        Usage:
            async for document in repo.find_stream({...}):
                process(document)

        Benefits:
            - Constant memory usage
            - Can start processing before query completes
            - Supports backpressure
        """
        collection = await self.get_collection()
        cursor = await collection.find(
            filters,
            limit=limit,
            batch_size=batch_size  # Fetch in batches
        )

        async for doc in cursor:
            yield self._validate(doc)  # Yield one at a time

    async def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        results = await self.find(filters, limit=1)
        return results[0] if results else None

    async def aql(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000
    ) -> List[T]:
        """
        Execute AQL query (buffers all results).

        For large results, use aql_stream() instead.
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars=bind_vars or {},
            batch_size=batch_size
        )

        results = []
        async for doc in cursor:
            results.append(self._validate(doc))

        return results

    async def aql_stream(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None,
        batch_size: int = 1000
    ):
        """
        Stream AQL query results.

        Example:
            query = "FOR doc IN some_collection FILTER doc.x > @value RETURN doc"
            async for result in repo.aql_stream(query, {"value": 10}):
                await process(result)
        """
        cursor = await self.db.aql.execute(
            query,
            bind_vars=bind_vars or {},
            batch_size=batch_size
        )

        async for doc in cursor:
            yield self._validate(doc)

    async def bulk_create(self, entities: List[T]) -> List[T]:
        """Batch create multiple documents."""
        if not entities:
            return []
        dumps = [
            e.model_dump(by_alias=True, exclude_none=True, mode="json")
            for e in entities
        ]
        collection = await self.get_collection()
        results = await collection.insert_many(
            dumps,
            return_new=True,
            overwrite=True,
        )
        return [self._validate(r["new"]) for r in results]
