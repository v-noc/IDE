import uuid
from pydantic import BaseModel, Field


from typing import Any, Optional, Dict, List
from app.core.model.properties import CodePosition


class CallSite(BaseModel):
    """Represents the location and context of a single call."""

    # Who made the call
    caller_frame: "CallFrame" = Field(..., exclude=True)

    # What was called (after alias resolution)
    callee_symbol: "Any" = Field(..., exclude=True)


class CallFrame(BaseModel):

    """Represents a single invocation on the call stack."""

    # Unique identifier for this specific call
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Where this call came from (Optional to break circular dependency)
    call_site: Optional[CallSite] = Field(default=None)

    # What function is being called
    callee_symbol: "Any" = Field(..., exclude=True)

    # SINGLE SOURCE OF TRUTH for this call's variables
    # - Arguments are symbols in this scope
    # - Local variables are symbols in this scope
    execution_scope: "Any" = Field(..., exclude=True)

    # What this specific invocation returned
    return_value: Optional["Any"] = Field(default=None, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def get_call_depth(self) -> int:
        """Calculate the depth of this call in the stack."""
        depth = 0
        frame = self.parent_frame
        while frame:
            depth += 1
            frame = frame.parent_frame
        return depth


class CallGraph(BaseModel):
    """
    The single source of truth for call relationships.
    Stores the actual graph structure without duplicating data elsewhere.
    """

    # The core graph: caller qualified name -> list of call sites
    edges: Dict[str, List[CallSite]] = Field(default_factory=dict)

    # Currently active call stack
    active_frames: List[CallFrame] = Field(default_factory=list, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def add_call(self, call_site: CallSite):
        """Add a call edge to the graph."""
        caller_qname = call_site.caller_frame.callee_symbol.qualified_name
        if caller_qname not in self.edges:
            self.edges[caller_qname] = []
        self.edges[caller_qname].append(call_site)

    def get_callees(self, caller_qname: str) -> List[CallSite]:
        """Get functions called by the specified caller."""
        return self.edges.get(caller_qname, [])

    def get_callers(self, callee_qname: str) -> List[CallSite]:
        """Get all call sites that call the specified function."""
        callers = []
        for sites in self.edges.values():
            for site in sites:
                if site.callee_symbol.qualified_name == callee_qname:
                    callers.append(site)
        return callers
