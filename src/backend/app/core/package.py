# src/backend/app/core/package.py

from .base import DomainObject
from ..models import node

from ..db import collections as db
from typing import Union,TYPE_CHECKING

if TYPE_CHECKING:
    from .code_elements import Function, Class
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

    @property
    def key(self) -> str:
        return self.model.key
    
    @property
    def path(self) -> str:
        return self.model.path
    
    def get_nodes_that_import_this(self) -> list[Union['Function', 'Class']]:
        """Returns all nodes that import this class."""
        from .code_elements import Function, Class
        import_edges = db.uses_import_edges.find({'to_id': self.id})
        result = []
        for edge in import_edges:
            node = db.nodes.get(edge.from_id)
            if node:
                if node.node_type == 'function':
                    result.append(Function(node))
                elif node.node_type == 'class':
                    result.append(Class(node))
        return result
