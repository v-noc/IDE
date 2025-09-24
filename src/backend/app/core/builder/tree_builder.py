
from typing import Dict, List, Any
from app.core.schemas.tree import AnyTreeNode, FolderTreeNode, ProjectTreeNode, FileTreeNode, ClassTreeNode, FunctionTreeNode, CallTreeNode

# Maps a node_type string to the correct Pydantic Tree model
NODE_TYPE_TO_TREE_MODEL_MAP = {
    "project": ProjectTreeNode,
    "folder": FolderTreeNode,
    "file": FileTreeNode,
    "class": ClassTreeNode,
    "function": FunctionTreeNode,
    "call": CallTreeNode,
}


class TreeBuilder:
    def __init__(self, flat_nodes: List[Dict[str, Any]]):
        self.flat_nodes = flat_nodes
        self.nodes_map: Dict[str, AnyTreeNode] = {}

    def build(self) -> List[AnyTreeNode]:
        """Constructs the tree and returns the root nodes."""
        if not self.flat_nodes:

            return []

        # First pass: Create all Pydantic model instances and map them by ID
        for item in self.flat_nodes:
            vertex_data = item["vertex"]
            node_type = vertex_data["node_type"]
            model_class = NODE_TYPE_TO_TREE_MODEL_MAP.get(node_type)

            if model_class:
                # If the query gave us a 'target', include it in the model
                if 'target' in item and item['target']:
                    vertex_data['target'] = item['target']

                node_instance = model_class.model_validate(vertex_data)
                self.nodes_map[node_instance.id] = node_instance

        # Second pass: Link children to their parents
        root_nodes = []

        for item in self.flat_nodes:
            node_id = item["vertex"]["_id"]
            parent_id = item["parent_id"]

            node = self.nodes_map.get(node_id)
            if not node:
                continue

            parent_node = self.nodes_map.get(parent_id)
            if parent_node:
                parent_node.children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes
