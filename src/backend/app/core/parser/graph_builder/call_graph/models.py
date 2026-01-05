from typing import List, Set, Optional, Dict
from dataclasses import dataclass
from app.core.model.nodes import CodePosition


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

    @property
    def all_active_targets(self) -> Set[str]:
        return self.added_target_ids | self.retained_target_ids
