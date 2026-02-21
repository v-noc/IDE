from typing import Any, Dict, List

from pydantic import BaseModel

from app.core.schemas.log_tree import LogTreeNode


class LogTreeBuilder:
    def __init__(self, flat_logs: List[Any]):
        self.flat_logs = flat_logs
        self.nodes_map: Dict[str, LogTreeNode] = {}

    @staticmethod
    def _to_dict(item: Any) -> Dict[str, Any]:
        if isinstance(item, BaseModel):
            return item.model_dump()
        return dict(item)

    @staticmethod
    def _child_ids(d: Dict[str, Any]) -> List[str]:
        raw = d.get("children_logs", [])
        if isinstance(raw, (set, list, tuple)):
            return [str(x) for x in raw if x]
        return []

    def build(self) -> List[LogTreeNode]:
        """Build tree from flat logs; each log has children_logs as string IDs."""
        if not self.flat_logs:
            return []

        child_ids_by_parent: Dict[str, List[str]] = {}
        for item in self.flat_logs:
            d = self._to_dict(item)
            node_id = d.get("id") or d.get("@id")
            if not node_id:
                continue

            # Exclude children_logs: raw logs have string IDs; tree expects nested nodes
            validate_d = {k: v for k, v in d.items() if k != "children_logs"}
            validate_d["children"] = []
            validate_d["function_id"] = d.get("function_id") or d.get("origin_function") or ""
            node = LogTreeNode.model_validate(validate_d)
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

        roots: List[LogTreeNode] = []
        seen: set[str] = set()
        for item in self.flat_logs:
            d = self._to_dict(item)
            nid = d.get("id") or d.get("@id")
            if not nid or nid in seen or nid in referenced:
                continue
            node = self.nodes_map.get(nid)
            if node:
                roots.append(node)
                seen.add(nid)
        return roots
