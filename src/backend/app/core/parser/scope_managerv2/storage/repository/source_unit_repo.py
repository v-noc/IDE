from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import SourceUnit


class SourceUnitRepository:
    """Repository for SourceUnit entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, source_unit: SourceUnit) -> SourceUnit:
        """Create and persist a new source unit."""
        self.session.add(source_unit)
        self.session.flush()
        return source_unit

    def get_by_id(self, source_unit_id: str) -> Optional[SourceUnit]:
        """Retrieve source by ID."""
        return self.session.query(SourceUnit).filter(SourceUnit.id == source_unit_id).first()

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

    def delete_by_id(self, source_unit_id: str) -> bool:
        """Delete a source unit."""
        source_unit = self.get_by_id(source_unit_id)
        if source_unit:
            self.session.delete(source_unit)
            return True
        return False

    def delete_by_path(self, file_path: str) -> bool:
        """Delete a source unit by file path."""
        source_unit = self.get_by_path(file_path)
        if source_unit:
            self.session.delete(source_unit)
            return True
        return False
