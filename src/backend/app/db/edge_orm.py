# src/backend/app/db/edge_orm.py

from typing import Type, TypeVar, Generic
from pydantic import BaseModel
from arango.collection import StandardCollection
from arango.database import StandardDatabase
from .client import get_db
from ..models.base import BaseEdge

T = TypeVar('T', bound=BaseEdge)

class ArangoEdgeCollection(Generic[T]):
    """
    A generic, typed wrapper around an ArangoDB edge collection that handles
    Pydantic model validation, creation, and retrieval.
    """
    def __init__(self, collection_name: str, model: Type[T]):
        self.collection_name = collection_name
        self.model = model
        self._collection: StandardCollection | None = None

    @property
    def db(self) -> StandardDatabase:
        """Get the current database connection."""
        return get_db()

    @property
    def collection(self) -> StandardCollection:
        """Memoized collection instance."""
        if self._collection is None:
            self._collection = self._get_or_create_collection()
        return self._collection

    def _validate(self, doc: dict) -> T:
        """Validate a document using the model."""
        return self.model.model_validate(doc)

    def _get_or_create_collection(self) -> StandardCollection:
        """
        Retrieves the edge collection or creates it if it doesn't exist.
        """
        if self.db.has_collection(self.collection_name):
            collection = self.db.collection(self.collection_name)
            if collection.properties()['edge']:
                return collection
            self.db.delete_collection(self.collection_name)
        
        return self.db.create_collection(self.collection_name, edge=True)

    def get(self, key: str) -> T | None:
        """
        Retrieves an edge by its key and validates it with the Pydantic model.
        """
        doc = self.collection.get(key)
        if doc:
            return self._validate(doc)
        return None

    def create(self, edge_data: T) -> T:
        """
        Inserts a new edge from a Pydantic model.
        """
        dump = edge_data.model_dump(by_alias=True, exclude_none=True)
        meta = self.collection.insert(dump, overwrite=True)
        new_doc = self.collection.get(meta["_key"])
        return self._validate(new_doc)

    def find(self, filters: dict, limit: int | None = None) -> list[T]:
        """
        Finds edges using a filter dictionary.
        """
        cursor = self.collection.find(filters, limit=limit)
        return [self._validate(doc) for doc in cursor]

    def truncate(self):
        """Deletes all edges in the collection."""
        self.collection.truncate()
