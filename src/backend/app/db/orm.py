from typing import Type, TypeVar, Generic
from arango.collection import StandardCollection
from pydantic import BaseModel
from datetime import datetime
from .client import get_db
from ..models.base import BaseDocument, BaseEdge

T = TypeVar("T", bound=BaseDocument)
E = TypeVar("E", bound=BaseEdge)

class CollectionManager(Generic[T]):
    def __init__(self, collection_name: str, model: Type[T]):
        self.collection_name = collection_name
        self.model = model
        self.db = get_db()
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> StandardCollection:
        if not self.db.has_collection(self.collection_name):
            return self.db.create_collection(self.collection_name)
        return self.db.collection(self.collection_name)

    def create(self, data: BaseModel) -> T:
        """Create a new document."""
        meta = self._collection.insert(data.model_dump())
        new_doc = self._collection.get(meta["_key"])
        return self.model(**new_doc)

    def get(self, key: str) -> T | None:
        doc = self._collection.get(key)
        if doc:
            return self.model(**doc)
        return None

    def find(self, filters: dict) -> list[T]:
        cursor = self._collection.find(filters)
        return [self.model(**doc) for doc in cursor]

    def update(self, key: str, data: BaseModel) -> T:
        """Update a document."""
        update_data = data.model_dump(exclude_unset=True)
        # Ensure updated_at is always current
        update_data["updated_at"] = datetime.utcnow()
        
        self._collection.update(key, update_data)
        updated_doc = self._collection.get(key)
        return self.model(**updated_doc)

    def delete(self, key: str) -> bool:
        return self._collection.delete(key)


class EdgeManager(Generic[E]):
    def __init__(self, collection_name: str, model: Type[E]):
        self.collection_name = collection_name
        self.model = model
        self.db = get_db()
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self) -> StandardCollection:
        if not self.db.has_collection(self.collection_name):
            return self.db.create_collection(self.collection_name, edge=True)
        return self.db.collection(self.collection_name)

    def create(self, from_doc_id: str, to_doc_id: str, data: BaseModel) -> E:
        """Create a new edge."""
        edge_data = data.model_dump()
        edge_data["_from"] = from_doc_id
        edge_data["_to"] = to_doc_id
        
        meta = self._collection.insert(edge_data)
        new_edge = self._collection.get(meta["_key"])
        return self.model(**new_edge)

    def get(self, key: str) -> E | None:
        edge = self._collection.get(key)
        if edge:
            return self.model(**edge)
        return None

    def find(self, filters: dict) -> list[E]:
        cursor = self._collection.find(filters)
        return [self.model(**doc) for doc in cursor]

    def update(self, key: str, data: BaseModel) -> E:
        """Update an edge."""
        update_data = data.model_dump(exclude_unset=True)
        # Ensure updated_at is always current
        update_data["updated_at"] = datetime.utcnow()
        
        self._collection.update(key, update_data)
        updated_edge = self._collection.get(key)
        return self.model(**updated_edge)

    def delete(self, key: str) -> bool:
        return self._collection.delete(key)
