# src/backend/app/db/orm.py

from typing import Type, TypeVar, Generic, Union, get_origin
from pydantic import BaseModel, TypeAdapter
from arango.collection import StandardCollection
from arango.database import StandardDatabase
from .client import get_db
from ..models.base import ArangoBase, BaseEdge

T = TypeVar('T', bound=ArangoBase)

class ArangoCollection(Generic[T]):
    """
    A generic, typed wrapper around an ArangoDB collection that handles
    Pydantic model validation, creation, and retrieval for both documents and edges.
    """
    _db: StandardDatabase | None = None

    def __init__(self, collection_name: str, model: Type[T]):
        self.collection_name = collection_name
        self.model = model
        
        # Use TypeAdapter for Unions or Annotated types containing Unions.
        # hasattr check is a reliable way to detect Annotated types.
        if get_origin(model) is Union or hasattr(model, '__metadata__'):
            self.adapter = TypeAdapter(model)
        else:
            self.adapter = None

        # Defer collection creation until it's first accessed.
        self._collection: StandardCollection | None = None

    @property
    def db(self) -> StandardDatabase:
        """Memoized database connection."""
        if self._db is None:
            self._db = get_db()
        return self._db

    @property
    def collection(self) -> StandardCollection:
        """Memoized collection instance."""
        if self._collection is None:
            # Default to creating a document collection. `create` will handle edges.
            self._collection = self._get_or_create_collection(edge=False)
        return self._collection

    def _validate(self, doc: dict) -> T:
        """Validate a document using the model or adapter."""
        if self.adapter:
            return self.adapter.validate_python(doc)
        return self.model.model_validate(doc)

    def _get_or_create_collection(self, edge: bool = False) -> StandardCollection:
        """
        Retrieves the collection or creates it if it doesn't exist.
        If the collection exists but has the wrong type (edge vs document),
        it is recreated.
        """
        if self.db.has_collection(self.collection_name):
            collection = self.db.collection(self.collection_name)
            # Return existing collection if type is correct
            if collection.properties()['edge'] is edge:
                return collection
            # Otherwise, delete it so it can be recreated with the correct type
            self.db.delete_collection(self.collection_name)

        return self.db.create_collection(self.collection_name, edge=edge)


    def get(self, key: str) -> T | None:
        """
        Retrieves a document by its key and validates it with the Pydantic model.
        Returns None if the document is not found.
        """
        doc = self.collection.get(key)
        if doc:
            return self._validate(doc)
        return None

    def create(self, doc_data: T) -> T:
        """
        Inserts a new document from a Pydantic model.
        Returns the fully populated, validated model from the database.
        """
        is_edge = isinstance(doc_data, BaseEdge)
        # Ensure collection is of the correct type before inserting
        self._collection = self._get_or_create_collection(edge=is_edge)

        dump = doc_data.model_dump(by_alias=True, exclude_none=True)
        meta = self.collection.insert(dump, overwrite=True)
        
        new_doc = self.collection.get(meta["_key"])
        return self._validate(new_doc)

    def update(self, key: str, patch_data: BaseModel) -> T:
        """
        Updates a document with new data.
        Returns the updated, validated model.
        """
        dump = patch_data.model_dump(exclude_unset=True)
        self.collection.update(key, dump)
        
        updated_doc = self.collection.get(key)
        return self._validate(updated_doc)

    def delete(self, key: str) -> bool:
        """
        Deletes a document by its key.
        Returns True if deletion was successful, False otherwise.
        """
        try:
            return self.collection.delete(key)
        except Exception:
            return False

    def find(self, filters: dict, limit: int | None = None) -> list[T]:
        """
        Finds documents using a filter dictionary.
        """
        cursor = self.collection.find(filters, limit=limit)
        return [self._validate(doc) for doc in cursor]

    def aql(self, query: str, bind_vars: dict | None = None) -> list[T]:
        """
        Executes a raw AQL query and validates the results against the model.
        """
        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return [self._validate(doc) for doc in cursor]

    def truncate(self):
        """
        Deletes all documents in the collection.
        """
        self.collection.truncate()
        
    def __getitem__(self, key: str) -> T | None:
        return self.get(key)
