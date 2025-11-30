import pytest
from unittest.mock import MagicMock, Mock
from app.core.parser.graph_builder.sync.graph_sync import MainGraphSyncService
from app.core.model.nodes import ProjectNode, FileNode, FolderNode, ClassNode, FunctionNode
from app.core.parser.graph_builder.collection.collector import CollectionResult
from app.core.parser.scope_manager.models import ScopeModel, ScopeType

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def project_node():
    return ProjectNode(
        name="test_project",
        description="Test Project",
        qname="test_project",
        current_version=1,
        path="/tmp/test_project"
    )

@pytest.fixture
def sync_service(mock_db, project_node):
    service = MainGraphSyncService(mock_db, project_node)
    # Mock repositories
    service.node_repo = MagicMock()
    service.edge_repo = MagicMock()
    return service

def test_sync_file_initial(sync_service):
    # Setup
    file_scope = ScopeModel(
        id="file_1",
        name="test.py",
        qname="test_project.test",
        type=ScopeType.FILE,
        file_path="/tmp/test_project/test.py",
        start_line=1, start_col=0, end_line=10, end_col=0
    )
    func_scope = ScopeModel(
        id="func_1",
        name="my_func",
        qname="test_project.test.my_func",
        type=ScopeType.FUNCTION,
        file_path="/tmp/test_project/test.py",
        start_line=2, start_col=0, end_line=5, end_col=0,
        parent_id="file_1"
    )
    
    result = CollectionResult(
        file_scope=file_scope,
        updated_scopes=[func_scope],
        removed_scope_ids=[],
        folder_changes=[]
    )

    # Mock node creation returns
    sync_service.node_repo.create.side_effect = lambda node: node
    sync_service.node_repo.find_by_qname.return_value = None # No existing folder
    
    # Mock project node ID for edge creation
    sync_service.project_node.id = "nodes/project_1"
    
    # Execute
    sync_service.sync_file(result)

    # Verify
    # 1. File Node Created
    assert sync_service.node_repo.create.call_count >= 2 # File + Function
    
    # Check File Node
    file_call = [c for c in sync_service.node_repo.create.call_args_list if isinstance(c[0][0], FileNode)][0]
    file_node = file_call[0][0]
    assert file_node.name == "test.py"
    assert file_node.qname == "test_project.test"
    
    # Check Function Node
    func_call = [c for c in sync_service.node_repo.create.call_args_list if isinstance(c[0][0], FunctionNode)][0]
    func_node = func_call[0][0]
    assert func_node.name == "my_func"
    
    # 2. Edges Created
    # Project -> File
    # File -> Function
    assert sync_service.edge_repo.create.call_count >= 2

def test_sync_file_with_folder(sync_service):
    # Setup
    file_scope = ScopeModel(
        id="file_2",
        name="utils.py",
        qname="test_project.core.utils",
        type=ScopeType.FILE,
        file_path="/tmp/test_project/core/utils.py",
        start_line=1, start_col=0, end_line=10, end_col=0
    )
    
    result = CollectionResult(
        file_scope=file_scope,
        updated_scopes=[],
        removed_scope_ids=[],
        folder_changes=[]
    )
    
    sync_service.node_repo.create.side_effect = lambda node: node
    sync_service.node_repo.find_by_qname.return_value = None # No existing folder
    sync_service.project_node.id = "nodes/project_1"

    # Execute
    sync_service.sync_file(result)

    # Verify Folder Creation
    folder_call = [c for c in sync_service.node_repo.create.call_args_list if isinstance(c[0][0], FolderNode)][0]
    folder_node = folder_call[0][0]
    assert folder_node.name == "core"
    assert folder_node.qname == "test_project.core"

def test_incremental_update_persistence(sync_service):
    # Setup - Simulate an update where a function is removed from code (not in updated_scopes)
    # But sync_service should NOT delete it.
    
    file_scope = ScopeModel(
        id="file_1",
        name="test.py",
        qname="test_project.test",
        type=ScopeType.FILE,
        file_path="/tmp/test_project/test.py",
        start_line=1, start_col=0, end_line=10, end_col=0
    )
    
    result = CollectionResult(
        file_scope=file_scope,
        updated_scopes=[], # Empty, so any previous children are "stale"
        removed_scope_ids=["func_old"],
        folder_changes=[]
    )
    
    sync_service.node_repo.create.side_effect = lambda node: node
    sync_service.project_node.id = "nodes/project_1"

    # Execute
    sync_service.sync_file(result)

    # Verify NO deletion calls
    sync_service.node_repo.delete.assert_not_called()
