# src/backend/app/db/collections/__init__.py

from ..node_orm import ArangoNodeCollection
from ..edge_orm import ArangoEdgeCollection
from ...models import node, edges

# ==============================================================================
# Node Collections
# ==============================================================================

# A single collection for all node types, distinguished by the 'node_type' field.
nodes = ArangoNodeCollection[node.Node](
    collection_name="nodes",
    model=node.Node
)

# ==============================================================================
# Edge Collections
# ==============================================================================

# Edge collection for linking a node to a project.
belongs_to_edges = ArangoEdgeCollection[edges.BelongsToEdge](
    collection_name="belongs_to",
    model=edges.BelongsToEdge
)

# Edge collection for representing containment (e.g., file in a folder).
contains_edges = ArangoEdgeCollection[edges.ContainsEdge](
    collection_name="contains",
    model=edges.ContainsEdge
)

# Edge collection for representing function/method calls.
calls_edges = ArangoEdgeCollection[edges.CallEdge](
    collection_name="calls",
    model=edges.CallEdge
)

# Edge collection for representing the usage of an import.
uses_import_edges = ArangoEdgeCollection[edges.UsesImportEdge](
    collection_name="uses_import",
    model=edges.UsesImportEdge
)

# Edge collection for linking a class to its method (a function).
implements_edges = ArangoEdgeCollection[edges.ImplementsEdge](
    collection_name="implements",
    model=edges.ImplementsEdge
)
