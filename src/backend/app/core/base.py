# src/backend/app/core/base.py

from typing import TypeVar, Generic
from ..models.base import ArangoBase

M = TypeVar('M', bound=ArangoBase)

class DomainObject(Generic[M]):
    """
    An abstract base class for domain objects. It wraps a Pydantic model
    and provides convenient access to its core attributes like `id` and `key`.
    """
    def __init__(self, model: M):
        if not model:
            raise ValueError("DomainObject cannot be initialized with a None model.")
        self.model = model

    @property
    def id(self) -> str:
        """Returns the document's unique ID (_id)."""
        if not self.model.id:
            raise ValueError("Model does not have an ID. It may not have been saved yet.")
        return self.model.id

    @property
    def key(self) -> str:
        """Returns the document's unique key (_key)."""
        if not self.model.key:
            raise ValueError("Model does not have a key. It may not have been saved yet.")
        return self.model.key
