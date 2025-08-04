from .base import BaseEdge
from .shared import NodePosition
from pydantic import Field, ConfigDict


class BelongsToEdge(BaseEdge):
    """Links a node to a project."""
    edge_type: str = "belongs_to"


class ContainsEdge(BaseEdge):
    """Represents that a node is contained within another 
    (e.g., file in a folder).
    """
    edge_type: str = "contains"
    position: NodePosition = Field(
        ..., description="The position of the contained node."
    )


class VirtualContainsEdge(BaseEdge):
    """Represents that a virtual folder is contained within another 
    (e.g., file in a folder).
    """
    edge_type: str = "virtual_contains"


class CallEdge(BaseEdge):
    """Represents a call from one node to another (e.g., function call)."""
    edge_type: str = "calls"
    order: int
    position: NodePosition = Field(
        ..., description="The position of the call in the source code."
    )


class UsesImportEdge(BaseEdge):
    """
    Represents the usage of an import, linking the consumer 
    (a function or class) to the provider (another function, class, 
    or an external package).
    """
    edge_type: str = "uses_import"
    target_symbol: str = Field(
        ..., 
        description="The specific symbol being imported (e.g., 'Request')."
    )
    target_qname: str = Field(
        ..., 
        description=(
            "The fully qualified name of the target module/package "
            "(e.g., 'requests.models')."
        )
    )
    alias: str | None = Field(
        None, description="The alias used for the import (e.g., 'np')."
    )
    import_position: NodePosition = Field(
        ..., description="The position of the 'import' statement."
    )
    usage_positions: list[NodePosition] = Field(
        default_factory=list, 
        description="A list of all positions where the import is used."
    )


class ImplementsEdge(BaseEdge):
    """Links a class to one of its methods (a function)."""
    edge_type: str = "implements"


class LinksToEdge(BaseEdge):
    """
    Creates a logical link from a virtual container (e.g., a virtual folder)
    to a code element.
    """
    edge_type: str = "links_to"

    model_config = ConfigDict(
        populate_by_name=True,
        # A virtual folder can only be linked to one code element.
        unique_on="_from",
    )
    