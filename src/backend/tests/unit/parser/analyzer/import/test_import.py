from app.core.schemas.tree import (
    ProjectNode,
    FileTreeNode,
    AnyTreeNode,
    CallTreeNode,
)


def find_file_node(nodes: list[AnyTreeNode], file_name: str) -> FileTreeNode | None:
    for node in nodes:
        if isinstance(node, FileTreeNode) and node.name == file_name:
            return node
        if hasattr(node, "children") and node.children:
            found = find_file_node(node.children, file_name)
            if found:
                return found
    return None


def test_absolute_path_import(project_tree: ProjectNode):
    file_node = find_file_node(project_tree.children, "import_absolute.py")

    assert file_node is not None
    assert len(file_node.children) == 2

    # Check for helper.create_user() call
    create_user_call = file_node.children[0]
    assert isinstance(create_user_call, CallTreeNode)
    assert create_user_call.name == "create_user"
    assert create_user_call.target is not None
    assert (
        create_user_call.target.qname == "sample_import.utils.helper.create_user"
    )

    # Check for User() instantiation
    user_call = file_node.children[1]
    assert isinstance(user_call, CallTreeNode)
    assert user_call.name == "__init__"
    assert user_call.target is not None
    assert user_call.target.qname == "sample_import.utils.data.user.User.__init__"
