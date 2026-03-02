from typing import Any, Dict, List

from pydantic import BaseModel

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

# Schema @type or Node class -> node_type for GroupTreeNode
GROUP_SCHEMA_TO_NODE_TYPE = {
    "CodeElementGroupSchema": "code_element_group",
    "CallGroupSchema": "call_group",
    "StructureGroupSchema": "structure_group",
    "CodeElementGroupNode": "code_element_group",
    "CallGroupNode": "call_group",
    "StructureGroupNode": "structure_group",
}

# Parent type -> allowed child types (for schema validation)
STRUCTURE_CHILDREN = (FolderTreeNode, FileTreeNode, GroupTreeNode)
CODE_CHILDREN = (ClassTreeNode, FunctionTreeNode, CallTreeNode, GroupTreeNode)
CALL_CHILDREN = (CallTreeNode, GroupTreeNode)


class TreeBuilder:
    def __init__(self, flat_nodes: List[Any]):
        self.flat_nodes = flat_nodes
        self.nodes_map: Dict[str, AnyTreeNode] = {}

    @staticmethod
    def _to_dict(item: Any) -> Dict[str, Any]:
        if isinstance(item, BaseModel):
            return item.model_dump()
        return dict(item)

    @staticmethod
    def _get_model_class(item: Any, d: Dict[str, Any]) -> type | None:
        schema = d.get("@type")
        if isinstance(schema, str):
            return SCHEMA_TO_TREE.get(schema)
        cls = getattr(item, "__class__", None)
        if cls is not None:
            return SCHEMA_TO_TREE.get(cls.__name__)
        return None

    @staticmethod
    def _child_ids(d: Dict[str, Any]) -> List[str]:
        raw = d.get("children", [])
        if isinstance(raw, (set, list, tuple)):
            return [str(x) for x in raw if x]
        return []

    @staticmethod
    def _is_valid_child(parent: AnyTreeNode, child: AnyTreeNode) -> bool:
        """Check if child type is valid for parent's children schema."""
        if isinstance(parent, (ProjectTreeNode, FolderTreeNode)):
            return isinstance(child, STRUCTURE_CHILDREN)
        if isinstance(parent, (FileTreeNode, ClassTreeNode, FunctionTreeNode)):
            return isinstance(child, CODE_CHILDREN)
        if isinstance(parent, CallTreeNode):
            return isinstance(child, CALL_CHILDREN)
        if isinstance(parent, GroupTreeNode):
            return isinstance(child, (GroupTreeNode, FolderTreeNode, FileTreeNode, ClassTreeNode, FunctionTreeNode, CallTreeNode))
        return True

    @staticmethod
    def _target_function_id(d: Dict[str, Any]) -> str | None:
        raw = d.get("target_function")
        if raw is None:
            return None
        if isinstance(raw, str) and raw:
            return raw
        if hasattr(raw, "id"):
            return str(getattr(raw, "id", None))
        if isinstance(raw, dict):
            return raw.get("id") or raw.get("@id")
        return str(raw) if raw else None

    def build(self) -> List[AnyTreeNode]:
        """Build tree from flat nodes; each node has children as string IDs."""
        if not self.flat_nodes:
            return []

        child_ids_by_parent: Dict[str, List[str]] = {}
        target_function_id_by_call: Dict[str, str] = {}
        for item in self.flat_nodes:

            d = self._to_dict(item)
            node_id = d.get("id") or d.get("@id")
            if not node_id:
                continue

            model_cls = self._get_model_class(item, d)
            if not model_cls:
                continue

            # Exclude children: raw nodes have string IDs; tree expects nested nodes
            validate_d = {k: v for k, v in d.items() if k != "children"}
            validate_d["children"] = []
            if model_cls == GroupTreeNode:
                schema = d.get("@type") or getattr(item, "__class__", None)
                if isinstance(schema, str):
                    node_type = GROUP_SCHEMA_TO_NODE_TYPE.get(schema)
                elif schema is not None:
                    node_type = GROUP_SCHEMA_TO_NODE_TYPE.get(schema.__name__)
                else:
                    node_type = None
                if node_type is not None:
                    validate_d["node_type"] = node_type
            node = model_cls.model_validate(validate_d)
            self.nodes_map[node.id] = node
            child_ids_by_parent[node.id] = self._child_ids(d)
            if model_cls == CallTreeNode:
                tid = self._target_function_id(d)
                if tid:
                    target_function_id_by_call[node.id] = tid

        referenced: set[str] = set()
        for pid, cids in child_ids_by_parent.items():
            parent = self.nodes_map.get(pid)
            if not parent:
                continue
            for cid in cids:
                child = self.nodes_map.get(cid)
                if child and self._is_valid_child(parent, child):
                    parent.children.append(child)
                    referenced.add(cid)

        for call_id, target_id in target_function_id_by_call.items():
            call_node = self.nodes_map.get(call_id)
            target_node = self.nodes_map.get(target_id)
            if (
                call_node
                and target_node
                and isinstance(call_node, CallTreeNode)
                and isinstance(target_node, (FunctionTreeNode, ClassTreeNode))
            ):
                target_node = target_node.model_copy(
                    update={"node_type": "function", "children": []})
                call_node.target = target_node

        roots: List[AnyTreeNode] = []
        seen: set[str] = set()
        for item in self.flat_nodes:
            d = self._to_dict(item)
            nid = d.get("id") or d.get("@id")
            if not nid or nid in seen or nid in referenced:
                continue
            node = self.nodes_map.get(nid)
            if node:
                roots.append(node)
                seen.add(nid)
        return roots
