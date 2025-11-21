# storage/writers/source_writer.py
"""
Source Writer - Handle creation and management of source files.
"""

import uuid
from ..storage.repository.repos import ScopeManagerRepository
from ..storage.models import SourceUnit


class SourceWriter:
    """Write operations for source files."""

    def __init__(self, repo: ScopeManagerRepository):
        self.repo = repo

    def create_source(
        self, file_path: str, content_hash: str = ""
    ) -> SourceUnit:
        """
        Create a new source file record.

        Args:
            file_path: The file path
            content_hash: Hash of file content

        Returns:
            The created source unit
        """
        source = SourceUnit(
            id=str(uuid.uuid4()),
            file_path=file_path,
            content_hash=content_hash,
        )
        return self.repo.sources.create(source)

    def update_source_hash(self, source_id: str, new_hash: str) -> bool:
        """
        Update the content hash for a source file.

        Args:
            source_id: The source ID
            new_hash: New content hash

        Returns:
            True if successful, False otherwise
        """
        source = self.repo.sources.get_by_id(source_id)
        if source:
            source.content_hash = new_hash
            return True
        return False
