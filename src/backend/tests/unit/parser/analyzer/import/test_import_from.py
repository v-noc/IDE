from app.core.schemas.tree import (
    ProjectNode,
    FileTreeNode,
    FolderTreeNode,
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


# def test_import_from_absolute_path(project_tree: ProjectNode):
#     file_node = find_file_node(project_tree.children, "main.py")
#     assert file_node is not None
#     assert len(file_node.children) == 1
#     call_node = file_node.children[0]
#     assert isinstance(call_node, CallTreeNode)
#     assert call_node.name == "create_user"
#     assert call_node.target is not None
#     assert call_node.target.qname == "sample_import.utils.helper.create_user"


def test_import_from_relative_path(project_tree: ProjectNode):
    file_node = find_file_node(project_tree.children, "import_relative")
    assert file_node is not None
    assert len(file_node.children) == 2

    call_node = [
        node for node in file_node.children if node.name == "create_user"][0]
    assert isinstance(call_node, CallTreeNode)
    assert call_node.name == "create_user"
    assert call_node.target is not None
    assert call_node.target.qname == "sample_import.utils.helper.create_user"

    user_call = [
        node for node in file_node.children if node.name == "User"][0]
    assert isinstance(user_call, CallTreeNode)
    assert user_call.name == "User"
    assert user_call.target is not None
    assert user_call.target.qname == "sample_import.utils.data.user.User"


def test_import_from_wildcard(project_tree: ProjectNode):
    # Test relative wildcard import
    file_node_relative = find_file_node(
        project_tree.children, "import_wild_card")
    assert file_node_relative is not None
    assert len(file_node_relative.children) == 1
    call_node_relative = [
        node for node in file_node_relative.children if node.name == "create_user"][0]
    assert isinstance(call_node_relative, CallTreeNode)
    assert call_node_relative.name == "create_user"
    assert call_node_relative.target is not None
    assert call_node_relative.target.qname == "sample_import.utils.helper.create_user"

    # Test absolute wildcard import
    file_node_absolute = find_file_node(
        project_tree.children, "import_wild_card_absolute"
    )
    assert file_node_absolute is not None
    assert len(file_node_absolute.children) == 1
    call_node_absolute = [
        node for node in file_node_absolute.children if node.name == "create_user"][0]
    assert isinstance(call_node_absolute, CallTreeNode)
    assert call_node_absolute.name == "create_user"
    assert call_node_absolute.target is not None
    assert call_node_absolute.target.qname == "sample_import.utils.helper.create_user"


def test_import_from_with_alias(project_tree: ProjectNode):
    file_node = find_file_node(project_tree.children, "import_alias")
    assert file_node is not None
    assert len(file_node.children) == 2
    call_node = [
        node for node in file_node.children if node.name == "make_user"][0]
    assert isinstance(call_node, CallTreeNode)
    assert call_node.name == "make_user"
    assert call_node.target is not None
    assert call_node.target.qname == "sample_import.utils.helper.create_user"


def test_import_from_init(project_tree: ProjectNode):
    file_node = find_file_node(project_tree.children, "init_import")

    assert len(file_node.children) == 2

    names = set()
    targets = set()
    for child in file_node.children:
        assert isinstance(child, CallTreeNode)
        names.add(child.name)
        targets.add(child.target.qname)

    assert names == {"create_user", "User"}
    assert targets == {"sample_import.utils.helper.create_user",
                       "sample_import.utils.data.user.User"}
