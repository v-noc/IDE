from ast import NodeVisitor


class CodeStructureVisitor(NodeVisitor):
    def __init__(self):
        self.root_nodes: List[BaseSchema] = []
        self._context_stack: List[ParentSchema] = []

    def get_root_nodes(self) -> List[BaseSchema]:
        return self.root_nodes

    def _add_node(self, node: BaseSchema):
        """Adds a node to the tree, linking it to the current parent."""
        if not self._context_stack:
            self.root_nodes.append(node)
        else:
