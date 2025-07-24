# src/backend/app/core/package.py

from .base import DomainObject
from ..models import node

class Package(DomainObject[node.PackageNode]):
    """
    A domain object representing an external package dependency.
    """
    @property
    def name(self) -> str:
        return self.model.name

    @property
    def version(self) -> str | None:
        return self.model.properties.version
