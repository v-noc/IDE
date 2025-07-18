from typing import Type, TypeVar, Generic
from arango.collection import StandardCollection
from pydantic import BaseModel
from datetime import datetime
from .client import get_db
from ..models.base import BaseDocument


T = TypeVar("T", bound=BaseDocument)


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
        """Create a new document with automatic timestamp"""
        now = datetime.utcnow()
        doc_data = data.model_dump()
        doc_data["_created"] = now.isoformat()
        doc_data["_updated"] = now.isoformat()
        
        meta = self._collection.insert(doc_data)
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
        """Update document with automatic timestamp"""
        now = datetime.utcnow()
        update_data = data.model_dump(exclude_unset=True)
        update_data["_updated"] = now.isoformat()
        
        self._collection.update(key, update_data)
        updated_doc = self._collection.get(key)
        return self.model(**updated_doc)

    def delete(self, key: str) -> bool:
        return self._collection.delete(key)
