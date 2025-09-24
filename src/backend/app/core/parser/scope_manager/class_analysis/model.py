from pydantic import BaseModel, Field

from __future__ import annotations
from typing import List, Dict, Any

from app.core.parser.scope_manager.core.scope import Scope


class ClassNode(BaseModel):
    """
    Represents a single class in the inheritance graph.
    """
    name: str  # The simple name of the class, e.g., "MyClass"
    qname: str  # The qualified name of the class, e.g., "module.MyClass"

    # The static scope of the class definition (keep excluded to avoid schema dependency).
    scope: Any = Field(..., exclude=True)

    # The qualified names of the direct base classes.
    base_classes: List[str] = Field(default_factory=list)

    # The computed Method Resolution Order (MRO).
    mro_list: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class InheritanceGraph(BaseModel):
    """
    Represents the complete inheritance hierarchy of all known classes.
    """

    # A mapping from qualified class names to their ClassNode representations.
    classes: Dict[str, ClassNode] = Field(default_factory=dict)

    def add_class(self, class_scope: Scope, base_qnames: List[str]):
        """
        Registers a new class in the graph.
        """
        qname = class_scope.qualified_name
        if qname in self.classes:
            # Class already registered, maybe update bases if needed
            self.classes[qname].base_classes = base_qnames
        else:
            self.classes[qname] = ClassNode(
                name=class_scope.name,
                qname=qname,
                scope=class_scope,
                base_classes=base_qnames
            )

    def get_class(self, qname: str) -> ClassNode:
        """
        Retrieves a class node by its qualified name.
        """
        if qname not in self.classes:
            raise ValueError(
                f"Class '{qname}' not found in the inheritance graph.")
        return self.classes[qname]
