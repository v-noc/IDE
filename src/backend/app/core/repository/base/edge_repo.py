from typing import Dict, Any, List, Optional
from .base_collection import BaseRepository
from pydantic import BaseModel
from typing import TypeVar,  List, Optional

T = TypeVar('T', bound=BaseModel)


class EdgeRepository(BaseRepository[T]):
    """Repository for edge collections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, is_edge=True, **kwargs)

    def find(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        # Map convenience fields to ArangoDB fields
        arango_filters = {}
        for key, value in filters.items():
            if key == 'from_id':
                arango_filters['_from'] = value
            elif key == 'to_id':
                arango_filters['_to'] = value
            else:
                arango_filters[key] = value

        cursor = self.collection.find(arango_filters, limit=limit)
        return [self._validate(doc) for doc in cursor]

    def find_one(self, filters: Dict[str, Any]) -> Optional[T]:
        results = self.find(filters, limit=1)
        return results[0] if results else None
