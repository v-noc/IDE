from typing import List
from sqlalchemy.orm import Session
from ..models import DependencyEdge


class DependencyEdgeRepository:
    """Repository for DependencyEdge entities."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, edge: DependencyEdge) -> DependencyEdge:
        """Create and persist a new dependency edge."""
        self.session.add(edge)
        self.session.flush()
        return edge

    def get_dependencies(self, source_id: str) -> List[DependencyEdge]:
        """Get all files this source depends on."""
        return (
            self.session.query(DependencyEdge)
            .filter(DependencyEdge.source_file_id == source_id)
            .all()
        )

    def get_dependents(self, source_id: str) -> List[DependencyEdge]:
        """Get all files that depend on this source."""
        return (
            self.session.query(DependencyEdge)
            .filter(DependencyEdge.target_file_id == source_id)
            .all()
        )

    def delete_dependencies_for_source(self, source_id: str) -> int:
        """Delete all dependencies for a source (Resync operation)."""
        count = (
            self.session.query(DependencyEdge)
            .filter(DependencyEdge.source_file_id == source_id)
            .delete()
        )
        return count
