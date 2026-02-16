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

    def build(self) -> List[AnyTreeNode]:
        """Build tree from flat nodes; each node has children as string IDs."""
        if not self.flat_nodes:
            return []

        child_ids_by_parent: Dict[str, List[str]] = {}
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
            node = model_cls.model_validate(validate_d)
            self.nodes_map[node.id] = node
            child_ids_by_parent[node.id] = self._child_ids(d)

        referenced: set[str] = set()
        for pid, cids in child_ids_by_parent.items():
            parent = self.nodes_map.get(pid)
            if not parent:
                continue
            for cid in cids:
                child = self.nodes_map.get(cid)
                if child:
                    parent.children.append(child)
                    referenced.add(cid)

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
