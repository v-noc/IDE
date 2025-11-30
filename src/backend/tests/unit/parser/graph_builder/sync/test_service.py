import unittest
from unittest.mock import MagicMock, patch
import sys
import types

# Mock arango package and submodules
arango_mock = types.ModuleType("arango")
arango_mock.database = types.ModuleType("arango.database")
arango_mock.collection = types.ModuleType("arango.collection")
arango_mock.exceptions = types.ModuleType("arango.exceptions")
arango_mock.database.StandardDatabase = MagicMock()
arango_mock.collection.StandardCollection = MagicMock()
arango_mock.exceptions.DocumentGetError = Exception
arango_mock.exceptions.DocumentDeleteError = Exception

sys.modules["arango"] = arango_mock
sys.modules["arango.database"] = arango_mock.database
sys.modules["arango.collection"] = arango_mock.collection
sys.modules["arango.exceptions"] = arango_mock.exceptions

from app.core.parser.graph_builder.sync.service import MainGraphSyncService
from app.core.parser.scope_manager.models import ScopeModel, ScopeType
from app.core.parser.graph_builder.collection.collector import CollectionResult
from app.core.model.nodes import ProjectNode


class TestMainGraphSyncService(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.project_node = ProjectNode(
            id="proj_1",
            path="/tmp/project",
            name="project",
            qname="project",
            description="Test Project",
            position={"line": 1, "column": 1, "end_line": 1, "end_column": 1}
        )
        
        # Mock repositories inside the service
        with patch("app.core.parser.graph_builder.sync.service.Repositories") as MockRepos, \
             patch("app.core.parser.graph_builder.sync.service.FileService") as MockFileService, \
             patch("app.core.parser.graph_builder.sync.service.FunctionService") as MockFuncService, \
             patch("app.core.parser.graph_builder.sync.service.ClassService") as MockClassService, \
             patch("app.core.parser.graph_builder.sync.service.ProjectService") as MockProjService:
            
            self.service = MainGraphSyncService(self.db, self.project_node)
            self.service.file_service = MockFileService.return_value
            self.service.function_service = MockFuncService.return_value
            self.service.class_service = MockClassService.return_value
            self.service.project_service = MockProjService.return_value

    def test_sync_file_upserts_nodes_and_edges(self):
        # Setup data
        file_scope = ScopeModel(
            id="file_1",
            name="test.py",
            qname="test.py",
            type=ScopeType.FILE,
            file_path="/tmp/project/test.py",
            start_line=1, start_col=1, end_line=10, end_col=1,
            checksum="hash1"
        )
        func_scope = ScopeModel(
            id="func_1",
            name="my_func",
            qname="test.py.my_func",
            type=ScopeType.FUNCTION,
            file_path="/tmp/project/test.py",
            start_line=2, start_col=1, end_line=5, end_col=1,
            parent_id="file_1"
        )
        
        result = CollectionResult(
            file_scope=file_scope,
            all_scopes=[func_scope],
            removed_scope_ids=[]
        )
        
        # Mock DB behavior
        self.service.file_service.get.return_value = None  # New file
        self.service.function_service.get.return_value = None  # New function
        
        # Mock _resolve_node_id to return valid IDs
        self.service._resolve_node_id = MagicMock(side_effect=lambda k: f"nodes/{k}")
        
        # Execute
        self.service.sync_file(result)
        
        # Verify File Upsert
        self.service.file_service.create.assert_called_once()
        
        # Verify Function Upsert
        self.service.function_service.create.assert_called_once()
        
        # Verify Edge Upsert (AQL execution)
        # We expect AQL calls for linking parent-child
        # And cleanup
        self.assertTrue(self.db.aql.execute.called)
        
        # Check if link_to_parent was called with a version
        # We can't easily check the exact AQL string, but we can check args
        calls = self.db.aql.execute.call_args_list
        
        # Find the link call
        link_call_found = False
        for call in calls:
            args, kwargs = call
            bind_vars = kwargs.get("bind_vars", {})
            if bind_vars.get("from_id") == "nodes/file_1" and \
               bind_vars.get("to_id") == "nodes/func_1" and \
               "version" in bind_vars:
                link_call_found = True
                break
        
        self.assertTrue(link_call_found, "Parent-child link edge not created")

    def test_cleanup_stale_edges(self):
        file_scope = ScopeModel(
            id="file_1",
            name="test.py",
            qname="test.py",
            type=ScopeType.FILE,
            file_path="/tmp/project/test.py",
            start_line=1, start_col=1, end_line=10, end_col=1,
            checksum="hash1"
        )
        result = CollectionResult(
            file_scope=file_scope,
            all_scopes=[],
            removed_scope_ids=[]
        )
        
        self.service._resolve_node_id = MagicMock(return_value="files/file_1")
        
        self.service.sync_file(result)
        
        # Verify cleanup AQL
        calls = self.db.aql.execute.call_args_list
        cleanup_call_found = False
        for call in calls:
            args, kwargs = call
            query = args[0]
            if "REMOVE e IN contains" in query:
                cleanup_call_found = True
                break
        
        self.assertTrue(cleanup_call_found, "Cleanup AQL not executed")

if __name__ == "__main__":
    unittest.main()
