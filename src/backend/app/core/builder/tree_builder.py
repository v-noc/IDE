from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from pydantic import BaseModel
from loguru import logger

from app.core.schemas.tree import (
    AnyTreeNode,
    CallTreeNode,
    ClassTreeNode,
    FileTreeNode,
    FolderTreeNode,
    FunctionTreeNode,
    GroupTreeNode,
    ProjectTreeNode,
)

# Schema @type or Node class -> tree model (nodes have children as string IDs; tree nodes have nested objects)
SCHEMA_TO_TREE = {
    "ProjectSchema": ProjectTreeNode,
    "FolderSchema": FolderTreeNode,
    "FileSchema": FileTreeNode,
    "ClassSchema": ClassTreeNode,
    "FunctionSchema": FunctionTreeNode,
    "CallSchema": CallTreeNode,
    "CodeElementGroupSchema": GroupTreeNode,
    "CallGroupSchema": GroupTreeNode,
    "StructureGroupSchema": GroupTreeNode,
    "ProjectNode": ProjectTreeNode,
    "FolderNode": FolderTreeNode,
    "FileNode": FileTreeNode,
    "ClassNode": ClassTreeNode,
    "FunctionNode": FunctionTreeNode,
    "CallNode": CallTreeNode,
    "CodeElementGroupNode": GroupTreeNode,
    "CallGroupNode": GroupTreeNode,
    "StructureGroupNode": GroupTreeNode,
}

# Schema @type or Node class -> group_type for GroupTreeNode
GROUP_SCHEMA_TO_GROUP_TYPE = {
    "CodeElementGroupSchema": "code_element_group",
    "CallGroupSchema": "call_group",
    "StructureGroupSchema": "structure_group",
    "CodeElementGroupNode": "code_element_group",
    "CallGroupNode": "call_group",
    "CallGroupSchema": "call_group",
    "StructureGroupNode": "structure_group",
}

# Parent type -> allowed child types (for schema validation)
STRUCTURE_CHILDREN = (FolderTreeNode, FileTreeNode, GroupTreeNode)
CODE_CHILDREN = (ClassTreeNode, FunctionTreeNode, CallTreeNode, GroupTreeNode)
CALL_CHILDREN = (CallTreeNode, GroupTreeNode)

# Nodes that may have code (or group) children loaded lazily when not in the payload.
_LAZY_CHILD_TRACKING_TYPES: Tuple[Type[Any], ...] = (
    FileTreeNode,
    ClassTreeNode,
    FunctionTreeNode,
    CallTreeNode,
    GroupTreeNode,
)


class TreeBuilder:
    def __init__(
        self,
        base_nodes: List[Any],
        compare_nodes: Optional[List[Any]] = None,
        target_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.base_nodes = base_nodes
        self.compare_nodes = compare_nodes
        self.target_lookup = target_lookup or {}
        self.status_map: Dict[str, str] = {}
        self.parent_map: Dict[str, str] = {}

    @staticmethod
    def _to_dict(item: Any) -> Dict[str, Any]:
        if isinstance(item, BaseModel):
            return item.model_dump()
        return dict(item)

    @staticmethod
    def _extract_id(d: Dict[str, Any]) -> Optional[str]:
        return d.get("id") or d.get("@id")

    @staticmethod
    def _extract_updated_at(d: Dict[str, Any]) -> Any:
        return d.get("updated_at")

    @staticmethod
    def _child_ids(d: Dict[str, Any]) -> List[str]:
        raw = d.get("children", [])
        if isinstance(raw, (set, list, tuple)):
            return [str(x) for x in raw if x]
        return []

    @staticmethod
    def _target_function_id(d: Dict[str, Any]) -> Optional[str]:
        raw = d.get("target_function")
        if raw is None:
            raw = d.get("target_class")
        if raw is None:
            return None
        if isinstance(raw, str) and raw:
            return raw
        if hasattr(raw, "id"):
            return str(getattr(raw, "id", None))
        if isinstance(raw, dict):
            return raw.get("id") or raw.get("@id")
        return str(raw) if raw else None

    def _call_target_tree_node(
        self, target_id: str
    ) -> Optional[Union[FunctionTreeNode, ClassTreeNode]]:
        existing = self.nodes_map.get(target_id)
        if existing and isinstance(
            existing, (FunctionTreeNode, ClassTreeNode)
        ):
            return existing.model_copy(
                update={"node_type": "function", "children": []}
            )
        raw = self.target_lookup.get(target_id)
        if not raw:
            return None
        model_cls = self._get_model_class(raw)
        if model_cls not in (FunctionTreeNode, ClassTreeNode):
            return None
        validate_d: Dict[str, Any] = {}
        for k, v in raw.items():
            if k == "children":
                continue
            if k == "@id":
                validate_d["id"] = v
            elif k == "@type":
                validate_d["type"] = v
                validate_d["schema_type"] = v
            else:
                validate_d[k] = v
        if "id" not in validate_d:
            return None
        validate_d["children"] = []
        validate_d["status"] = self.status_map.get(
            validate_d["id"], "unchanged"
        )
        try:
            node = model_cls.model_validate(validate_d)
            return node.model_copy(
                update={"node_type": "function", "children": []}
            )
        except Exception as e:
            logger.error(
                f"Error validating lookup target {target_id}: {e}"
            )
            return None

    @staticmethod
    def _get_model_class(item: Any) -> type | None:
        schema = item.get("@type")
        if schema is None:
            item_id = item.get("id") or item.get("@id")
            if item_id is not None:
                schema = item_id.split("/")[0]

        if isinstance(schema, str):
            return SCHEMA_TO_TREE.get(schema)
        cls = getattr(item, "__class__", None)

        if cls is not None:
            return SCHEMA_TO_TREE.get(cls.__name__)
        return None

    @staticmethod
    def _is_valid_child(parent: AnyTreeNode, child: AnyTreeNode) -> bool:
        STRUCTURE_CHILDREN = (FolderTreeNode, FileTreeNode, GroupTreeNode)
        CODE_CHILDREN = (ClassTreeNode, FunctionTreeNode,
                         CallTreeNode, GroupTreeNode)
        CALL_CHILDREN = (CallTreeNode, GroupTreeNode)

        if isinstance(parent, (ProjectTreeNode, FolderTreeNode)):
            return isinstance(child, STRUCTURE_CHILDREN)
        if isinstance(parent, (FileTreeNode, ClassTreeNode, FunctionTreeNode)):
            return isinstance(child, CODE_CHILDREN)
        if isinstance(parent, CallTreeNode):
            return isinstance(child, CALL_CHILDREN)
        if isinstance(parent, GroupTreeNode):
            return isinstance(child, (
                GroupTreeNode, FolderTreeNode, FileTreeNode,
                ClassTreeNode, FunctionTreeNode, CallTreeNode
            ))
        return True

    def _build_parent_map(self, nodes: List[Any]) -> Dict[str, str]:
        """Build child_id -> parent_id mapping."""
        parent_map = {}
        for item in nodes:
            d = self._to_dict(item)
            pid = self._extract_id(d)
            if pid:
                for cid in self._child_ids(d):
                    parent_map[cid] = pid
        return parent_map

    def _compute_statuses(
        self,
        base_idx: Dict[str, Dict[str, Any]],
        compare_idx: Dict[str, Dict[str, Any]],
        base_parent_map: Dict[str, str],
        compare_parent_map: Dict[str, str],
    ) -> Set[str]:
        """Compute statuses and return set of added node IDs."""
        added_ids: Set[str] = set()

        # Check base nodes
        for nid, d in base_idx.items():
            if nid in compare_idx:
                # Check if parent changed (moved)
                base_parent = base_parent_map.get(nid)
                compare_parent = compare_parent_map.get(nid)

                if base_parent != compare_parent:
                    self.status_map[nid] = "moved"
                else:
                    # Same parent, check content modification
                    base_updated = self._extract_updated_at(d)
                    compare_updated = self._extract_updated_at(
                        compare_idx[nid])
                    if base_updated != compare_updated:
                        self.status_map[nid] = "modified"
                    else:
                        self.status_map[nid] = "unchanged"
            else:
                self.status_map[nid] = "removed"

        # Identify added nodes
        for nid in compare_idx:
            if nid not in base_idx:
                self.status_map[nid] = "added"
                added_ids.add(nid)

        return added_ids

    def _inject_added_nodes(
        self,
        base_dict: Dict[str, Dict[str, Any]],
        added_ids: Set[str],
        compare_idx: Dict[str, Dict[str, Any]],
        compare_parent_map: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Inject added nodes into base structure and return merged list."""
        # Deep copy base nodes to avoid mutating originals

        merged = {nid: dict(d) for nid, d in base_dict.items()}

        # Add added nodes to the pool
        for nid in added_ids:
            merged[nid] = dict(compare_idx[nid])

        # Inject added nodes into their parents' children lists
        for nid in added_ids:
            parent_id = compare_parent_map.get(nid)
            if not parent_id or parent_id not in merged:
                continue

            parent_dict = merged[parent_id]
            current_children = parent_dict.get("children", [])

            # Normalize to list
            if isinstance(current_children, (set, tuple)):
                current_children = list(current_children)
            elif not isinstance(current_children, list):
                current_children = []

            # Add if not present
            if nid not in current_children:
                parent_dict["children"] = current_children + [nid]

        return list(merged.values())

    def _propagate_statuses(self, nodes_map: Dict[str, AnyTreeNode]) -> None:
        """Bubble up changes: if child is added/removed/modified/moved, parent becomes modified."""
        changed_ids = {
            nid for nid, status in self.status_map.items()
            if status in ("added", "removed", "modified", "moved")
        }

        for nid in changed_ids:
            current = nid
            while current in self.parent_map:
                parent_id = self.parent_map[current]
                parent_node = nodes_map.get(parent_id)
                if parent_node and parent_node.status == "unchanged":
                    parent_node.status = "modified"
                    self.status_map[parent_id] = "modified"
                current = parent_id

    def build(self) -> List[AnyTreeNode]:
        """Build tree preserving base structure with diff statuses."""
        if not self.base_nodes:
            return []

        # Index base nodes
        base_idx: Dict[str, Dict[str, Any]] = {}
        for item in self.base_nodes:
            d = self._to_dict(item)
            nid = self._extract_id(d)
            if nid:
                base_idx[nid] = d

        # Index compare nodes if provided
        compare_idx: Dict[str, Dict[str, Any]] = {}
        if self.compare_nodes:
            for item in self.compare_nodes:
                d = self._to_dict(item)
                nid = self._extract_id(d)
                if nid:
                    compare_idx[nid] = d

        # Build parent maps for both versions
        base_parent_map = self._build_parent_map(self.base_nodes)
        compare_parent_map = self._build_parent_map(
            self.compare_nodes) if self.compare_nodes else {}

        # Compute statuses and get added IDs
        added_ids: Set[str] = set()
        if self.compare_nodes:
            added_ids = self._compute_statuses(
                base_idx, compare_idx, base_parent_map, compare_parent_map
            )
            # Prepare merged nodes (base structure + injected additions)
            node_dicts = self._inject_added_nodes(
                base_idx, added_ids, compare_idx, compare_parent_map
            )

        else:
            node_dicts = list(base_idx.values())

        # Build the tree from prepared nodes
        result = self._build_tree_from_dicts(node_dicts)

        return result

    def _build_tree_from_dicts(self, node_dicts: List[Dict[str, Any]]) -> List[AnyTreeNode]:
        """Build tree from prepared node dictionaries."""
        if not node_dicts:
            return []

        self.nodes_map = {}
        self.parent_map = {}
        child_ids_by_parent: Dict[str, List[str]] = {}
        target_function_id_by_call: Dict[str, str] = {}

        # Phase 1: Create node instances
        for d in node_dicts:
            node_id = self._extract_id(d)
            if not node_id:

                continue

            model_cls = self._get_model_class(d)
            if not model_cls:

                continue

            # Prepare validation data - normalize @id/@type to id/type
            validate_d: Dict[str, Any] = {}
            for k, v in d.items():
                if k == "children":
                    continue
                # Normalize JSON-LD keys to Pydantic field names
                if k == "@id":
                    validate_d["id"] = v
                elif k == "@type":
                    # or keep as @type if your model has it
                    validate_d["type"] = v
                    # Also store original for schema lookup if needed
                    validate_d["schema_type"] = v
                else:
                    validate_d[k] = v

            # Ensure id is set
            if "id" not in validate_d:
                logger.warning(f"Skipping node without id: {d}")
                continue

            validate_d["children"] = []

            # Apply status from map
            validate_d["status"] = self.status_map.get(node_id, "unchanged")

            # Handle group type for GroupTreeNode
            if model_cls == GroupTreeNode:
                schema = d.get("@type") or d.get("schema_type")
                if isinstance(schema, str):
                    group_type = GROUP_SCHEMA_TO_GROUP_TYPE.get(schema)
                    if group_type:
                        validate_d["group_type"] = group_type

            try:
                node = model_cls.model_validate(validate_d)
                self.nodes_map[node_id] = node
                child_ids_by_parent[node_id] = self._child_ids(d)

                if model_cls == CallTreeNode:
                    tid = self._target_function_id(d)
                    if tid:
                        target_function_id_by_call[node_id] = tid
            except Exception as e:
                logger.error(
                    f"Error validating {node_id} of class {model_cls}: {e}")
                continue

        # Phase 2: Link children and build parent map
        referenced: Set[str] = set()
        for pid, cids in child_ids_by_parent.items():
            parent = self.nodes_map.get(pid)
            if not parent:
                continue

            for cid in cids:
                child = self.nodes_map.get(cid)
                if child and self._is_valid_child(parent, child):
                    parent.children.append(child)
                    self.parent_map[cid] = pid
                    referenced.add(cid)

            if isinstance(parent, _LAZY_CHILD_TRACKING_TYPES):
                attached_ids = {c.id for c in parent.children}
                lazy = [cid for cid in cids if cid not in attached_ids]
                if lazy:
                    parent.lazy_child_ids = lazy

        # Phase 3: Link call targets (nodes_map first, else target_lookup)
        for call_id, target_id in target_function_id_by_call.items():
            call_node = self.nodes_map.get(call_id)
            if not call_node or not isinstance(call_node, CallTreeNode):
                continue
            target_copy = self._call_target_tree_node(target_id)
            if target_copy:
                call_node.target = target_copy

        # Phase 4: Propagate statuses upward
        if self.compare_nodes:
            self._propagate_statuses(self.nodes_map)

        # Phase 5: Identify roots
        roots: List[AnyTreeNode] = []
        seen: Set[str] = set()
        for d in node_dicts:
            nid = self._extract_id(d)
            if not nid or nid in seen or nid in referenced:
                continue
            node = self.nodes_map.get(nid)
            if node:
                roots.append(node)
                seen.add(nid)

        return roots
