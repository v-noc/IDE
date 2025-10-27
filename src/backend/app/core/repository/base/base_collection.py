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
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.exceptions import DocumentGetError
from datetime import datetime, timezone

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common functionality."""

    def __init__(
        self,
        db: StandardDatabase,
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
        self._ensure_collection()
        # Handle discriminated unions
        if get_origin(model) is Union or hasattr(model, "__metadata__"):
            self.adapter = TypeAdapter(model)
        else:
            self.adapter = None

    @property
    def collection(self) -> StandardCollection:
        if self._collection is None:
            self._collection = self._ensure_collection()
        return self._collection

    def _validate(self, doc: Dict[str, Any]) -> T:
        if self.adapter:
            return self.adapter.validate_python(doc)
        return self.model.model_validate(doc)

    def _ensure_collection(self) -> StandardCollection:
        if self.db.has_collection(self.collection_name):
            collection = self.db.collection(self.collection_name)
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
            collection = self.db.create_collection(
                self.collection_name,
                edge=self.is_edge,
                **self.key_options,  # This unpacks the dict
            )

        # Apply indexes
        for index_spec in self.indexes:
            try:
                # Add logging here if you have a logger configured
                collection.add_hash_index(
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

    def get_by_key(self, key: str) -> Optional[T]:
        try:
            doc = self.collection.get(key)
            return self._validate(doc) if doc else None
        except DocumentGetError:
            return None

    def get_raw_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a document by its key without Pydantic validation."""
        return self.collection.get(key)

    def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get by full document ID (collection/key)."""
        key = doc_id.split("/")[-1] if "/" in doc_id else doc_id
        return self.get_by_key(key)

    def create(self, entity: T) -> T:
        """Create a document and return the newly created version."""
        dump = entity.model_dump(by_alias=True, exclude_none=True, mode="json")
        # Get the full created document back in one call
        meta = self.collection.insert(
            dump,
            return_new=True,
            overwrite=True,
        )
        return self._validate(meta["new"])

    def update(self, key: str, entity: T) -> T:
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
        meta = self.collection.update(
            document,
            return_new=True,
        )
        return self._validate(meta["new"])

    def delete(self, key: str) -> bool:
        try:
            self.collection.delete(key)
            return True
        except DocumentGetError:
            return False

    def find(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[T]:
        cursor = self.collection.find(
            filters,
            limit=limit,
        )
        return [self._validate(doc) for doc in cursor]

    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        results = self.find(filters, limit=1)
        return results[0] if results else None

    def aql(
        self,
        query: str,
        bind_vars: Optional[Dict[str, Any]] = None,
    ) -> List[T]:
        cursor = self.db.aql.execute(
            query,
            bind_vars=bind_vars or {},
        )
        return [self._validate(doc) for doc in cursor]
