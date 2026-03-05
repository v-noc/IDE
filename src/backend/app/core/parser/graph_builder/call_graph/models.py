from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
from dataclasses import field
from app.core.model.nodes import CodePosition, CallNode


@dataclass
class ResolvedCall:
    """Represents a successfully resolved call within a specific scope."""
    target_id: str  # e.g., "nodes/<target_id>"
    target_qname: str
    call_node_name: str  # e.g., "my_func"
    position: CodePosition


@dataclass
class ScopeSyncResult:
    """Result of synchronizing a scope, used for recursion."""
    parent_id: str
    added_target_ids: Set[str]
    retained_target_ids: Set[str]
    removed_target_ids: Set[str]
    created_map: Dict[str, str]
    calls_to_create: List[CallNode] = field(default_factory=list)
    moves_to_execute: List[Tuple[str, str, str]] = field(default_factory=list)
    call_ids_to_remove: List[str] = field(default_factory=list)

    @property
    def all_active_targets(self) -> Set[str]:
        return self.added_target_ids | self.retained_target_ids
