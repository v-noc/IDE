# # src/backend/app/db/collections/__init__.py
# from app.core.model import nodes, edges

# from ..node_orm import ArangoNodeCollection
# from ..edge_orm import ArangoEdgeCollection

# # ==============================================================================
# # Node Collections
# # ==============================================================================

# # A single collection for all node types, distinguished by the 'node_type' field.
# nodes = ArangoNodeCollection[nodes.Node](
#     collection_name="nodes",
#     model=nodes.Node
# )

# # ==============================================================================
# # Edge Collections
# # ==============================================================================

# # Edge collection for linking a node to a project.
# belongs_to_edges = ArangoEdgeCollection[edges.BelongsTo](
#     collection_name="belongs_to",
#     model=edges.BelongsToEdge
# )

# # Edge collection for linking a virtual folder to a code element.
# links_to_edges = ArangoEdgeCollection[edges.LinksTo](
#     collection_name="links_to",
#     model=edges.LinksToEdge
# )

# # Edge collection for representing containment (e.g., file in a folder).
# contains_edges = ArangoEdgeCollection[edges.Contains](
#     collection_name="contains",
#     model=edges.ContainsEdge
# )

# # Edge collection for representing virtual containment (e.g., file in a virtual folder).
# virtual_contains_edges = ArangoEdgeCollection[edges.VirtualContains](
#     collection_name="virtual_contains",
#     model=edges.VirtualContainsEdge
# )

# # Edge collection for representing function/method calls.
# calls_edges = ArangoEdgeCollection[edges.Call](
#     collection_name="calls",
#     model=edges.CallEdge
# )

# # Edge collection for representing the usage of an import.
# uses_import_edges = ArangoEdgeCollection[edges.UsesImport](
#     collection_name="uses_import",
#     model=edges.UsesImportEdge
# )

# # Edge collection for linking a class to its method (a function).
# implements_edges = ArangoEdgeCollection[edges.Implements](
#     collection_name="implements",
#     model=edges.ImplementsEdge
# )
