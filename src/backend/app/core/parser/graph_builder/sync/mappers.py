from app.core.model.properties import CodePosition
from app.core.parser.scope_manager.models import ScopeModel
from app.core.model.nodes import FileNode, FolderNode, ClassNode, FunctionNode


def map_scope_to_position(scope: ScopeModel) -> CodePosition:
    """Map ScopeModel position fields to CodePosition."""
    return CodePosition(
        line_no=scope.start_line,
        col_offset=scope.start_col,
        end_line_no=scope.end_line,
        end_col_offset=scope.end_col,
    )


def map_scope_to_file_node(scope: ScopeModel, version: int) -> FileNode:
    """Map ScopeModel to FileNode."""
    return FileNode(
        id=scope.id,
        name=scope.name,
        description=f"File: {scope.name}",
        qname=scope.qname,
        current_version=version,

        path=scope.file_path,
        hash=scope.checksum or "",
    )


def map_scope_to_folder_node(scope: ScopeModel, version: int) -> FolderNode:
    """Map ScopeModel to FolderNode."""
    return FolderNode(
        id=scope.id,
        name=scope.name,
        description=f"Folder: {scope.name}",
        qname=scope.qname,
        current_version=version,
        path=scope.file_path,  # For folders, file_path is the folder path
    )


def map_scope_to_class_node(scope: ScopeModel, version: int) -> ClassNode:
    """Map ScopeModel to ClassNode."""
    return ClassNode(
        id=scope.id,
        name=scope.name,
        description=f"Class: {scope.name}",
        qname=scope.qname,
        current_version=version,

        position=map_scope_to_position(scope),
        implements=scope.mro,  # Using MRO as implements for now
    )


def map_scope_to_function_node(
    scope: ScopeModel, version: int
) -> FunctionNode:
    """Map ScopeModel to FunctionNode."""
    return FunctionNode(
        name=scope.name,
        id=scope.id,
        description=f"Function: {scope.name}",
        qname=scope.qname,
        current_version=version,

        position=map_scope_to_position(scope),
    )
