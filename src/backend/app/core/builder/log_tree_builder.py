from typing import Dict, List, Any

from app.core.schemas.log_tree import LogTreeNode


class LogTreeBuilder:
    def __init__(self, flat_logs: List[Dict[str, Any]]):
        self.flat_logs = flat_logs
        self.nodes_map: Dict[str, LogTreeNode] = {}

    def build(self) -> List[LogTreeNode]:
        if not self.flat_logs:
            return []

        # Create nodes
        for item in self.flat_logs:
            vertex = item["vertex"]
            function_id = item["function_id"]

            if not function_id:
                function_id = ""
            node = LogTreeNode.model_validate(
                {**vertex, "function_id": function_id}
            )

            self.nodes_map[node.id] = node

        # Link children via parent_id
        roots: List[LogTreeNode] = []
        for item in self.flat_logs:
            node_id = item["vertex"]["_id"]
            parent_id = item.get("parent_id")
            node = self.nodes_map.get(node_id)
            if not node:
                continue
            parent = self.nodes_map.get(parent_id)
            if parent:
                parent.children.append(node)
            else:
                roots.append(node)

        return roots
