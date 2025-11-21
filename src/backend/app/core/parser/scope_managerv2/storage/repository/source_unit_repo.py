from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import SourceUnit


class SourceRepository:
    """Repository for SourceUnit entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, source: SourceUnit) -> SourceUnit:
        """Create and persist a new source unit."""
        self.session.add(source)
        self.session.flush()
        return source

    def get_by_id(self, source_id: str) -> Optional[SourceUnit]:
        """Retrieve source by ID."""
        return self.session.query(SourceUnit).filter(SourceUnit.id == source_id).first()

    def get_by_path(self, file_path: str) -> Optional[SourceUnit]:
        """Retrieve source by file path."""
        return (
            self.session.query(SourceUnit)
            .filter(SourceUnit.file_path == file_path)
            .first()
        )

    def get_all(self) -> List[SourceUnit]:
        """Get all source units."""
        return self.session.query(SourceUnit).all()

    def delete_by_id(self, source_id: str) -> bool:
        """Delete a source unit."""
        source = self.get_by_id(source_id)
        if source:
            self.session.delete(source)
            return True
        return False
