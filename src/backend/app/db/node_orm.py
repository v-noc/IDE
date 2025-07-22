# src/backend/app/db/node_orm.py

from typing import Type, TypeVar, Generic, Union, get_origin
from pydantic import BaseModel, TypeAdapter
from arango.collection import StandardCollection
from arango.database import StandardDatabase
from .client import get_db
from ..models.base import ArangoBase
from .edge_orm import ArangoEdgeCollection

T = TypeVar('T', bound=ArangoBase)

class ArangoNodeCollection(Generic[T]):
    """
    A generic, typed wrapper around an ArangoDB document collection that handles
    Pydantic model validation, creation, and retrieval.
    """
    def __init__(self, collection_name: str, model: Type[T]):
        self.collection_name = collection_name
        self.model = model
        
        if get_origin(model) is Union or hasattr(model, '__metadata__'):
            self.adapter = TypeAdapter(model)
        else:
            self.adapter = None

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
        """Validate a document using the model or adapter."""
        if self.adapter:
            return self.adapter.validate_python(doc)
        return self.model.model_validate(doc)

    def _get_or_create_collection(self) -> StandardCollection:
        """
        Retrieves the document collection or creates it if it doesn't exist.
        """
        if self.db.has_collection(self.collection_name):
            collection = self.db.collection(self.collection_name)
            if not collection.properties()['edge']:
                return collection
            self.db.delete_collection(self.collection_name)

        return self.db.create_collection(self.collection_name, edge=False)

    def get(self, key: str) -> T | None:
        """
        Retrieves a document by its key and validates it with the Pydantic model.
        """
        doc = self.collection.get(key)
        if doc:
            return self._validate(doc)
        return None

    def create(self, doc_data: T) -> T:
        """
        Inserts a new document from a Pydantic model.
        """
        dump = doc_data.model_dump(by_alias=True, exclude_none=True)
        meta = self.collection.insert(dump, overwrite=True)
        new_doc = self.collection.get(meta["_key"])
        return self._validate(new_doc)
    
    def update(self, doc_data: T) -> T:
        """
        Updates an existing document from a Pydantic model.
        """
        dump = doc_data.model_dump(by_alias=True, exclude_none=True)
        self.collection.update(dump)

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
        """Deletes all documents in the collection."""
        self.collection.truncate()

    def find_related(
        self,
        start_node_id: str,
        edge_collection: "ArangoEdgeCollection",
        direction: str = "outbound",
        filter_by_type: str | None = None
    ) -> list[T]:
        """
        Finds nodes related to a starting node through a given edge collection.
        """
        if direction not in ["outbound", "inbound", "any"]:
            raise ValueError("Direction must be 'outbound', 'inbound', or 'any'.")

        query = f"""
        FOR node IN 1..1 {direction.upper()} @start_node_id @@edge_collection
        """
        bind_vars = {
            "start_node_id": start_node_id,
            "@edge_collection": edge_collection.collection_name
        }

        if filter_by_type:
            query += " FILTER node.node_type == @node_type"
            bind_vars["node_type"] = filter_by_type
        
        query += " RETURN node"

        return self.aql(query, bind_vars)
        
    def __getitem__(self, key: str) -> T | None:
        return self.get(key)

    def get_all_descendants(self, start_node_id: str, edge_collection: "ArangoEdgeCollection") -> list[T]:
        """
        Retrieves all descendants of a starting node.
        """
        query = """
        FOR node IN 1..10 OUTBOUND @start_node_id @@edge_collection
            RETURN node
        """
        bind_vars = {
            "start_node_id": start_node_id,
            "@edge_collection": edge_collection.collection_name
        }
        return self.aql(query, bind_vars)