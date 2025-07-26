from src.backend.app.core.parser.python.symbol_table import SymbolTable


class TestSymbolTable:
    """
    Unit tests for the SymbolTable class, focusing on Phase 2 functionality
    for import resolution and local vs external package differentiation.
    """

    def test_add_symbol(self):
        """Test basic symbol addition functionality."""
        symbol_table = SymbolTable()
        
        symbol_table.add_symbol("my_project.utils", "file_123")
        symbol_table.add_symbol("my_project.main", "file_456")
        
        assert symbol_table.get_symbol_id("my_project.utils") == "file_123"
        assert symbol_table.get_symbol_id("my_project.main") == "file_456"
        assert symbol_table.get_symbol_id("nonexistent") is None

    def test_add_import(self):
        """Test import registration functionality."""
        symbol_table = SymbolTable()
        
        # Add imports for a file
        symbol_table.add_import("file_123", "Request", "fastapi.Request")
        symbol_table.add_import("file_123", "np", "numpy")
        symbol_table.add_import("file_456", "json", "json")
        
        # Check file imports
        file_123_imports = symbol_table.get_file_imports("file_123")
        assert file_123_imports == {
            "Request": "fastapi.Request",
            "np": "numpy"
        }
        
        file_456_imports = symbol_table.get_file_imports("file_456")
        assert file_456_imports == {"json": "json"}
        
        # Check nonexistent file
        assert symbol_table.get_file_imports("nonexistent") == {}

    def test_resolve_import_qname(self):
        """Test import name resolution."""
        symbol_table = SymbolTable()
        
        # Add imports
        symbol_table.add_import("file_123", "Request", "fastapi.Request")
        symbol_table.add_import("file_123", "np", "numpy")
        symbol_table.add_import("file_123", "local_utils", "my_project.utils")
        
        # Test successful resolution
        assert (symbol_table.resolve_import_qname("file_123", "Request") 
                == "fastapi.Request")
        assert symbol_table.resolve_import_qname("file_123", "np") == "numpy"
        assert (symbol_table.resolve_import_qname("file_123", "local_utils") 
                == "my_project.utils")
        
        # Test unsuccessful resolution
        assert (symbol_table.resolve_import_qname("file_123", "nonexistent") 
                is None)
        assert (symbol_table.resolve_import_qname("nonexistent_file", "Request") 
                is None)

    def test_is_local_module_exact_match(self):
        """Test local module detection with exact matches."""
        symbol_table = SymbolTable()
        
        # Add some local symbols
        symbol_table.add_symbol("my_project", "project_123")
        symbol_table.add_symbol("my_project.utils", "file_456")
        symbol_table.add_symbol("my_project.models.user", "file_789")
        
        # Test exact matches
        assert symbol_table.is_local_module("my_project") is True
        assert symbol_table.is_local_module("my_project.utils") is True
        assert symbol_table.is_local_module("my_project.models.user") is True
        
        # Test non-local packages
        assert symbol_table.is_local_module("fastapi") is False
        assert symbol_table.is_local_module("numpy") is False

    def test_is_local_module_prefix_match(self):
        """Test local module detection with prefix matching."""
        symbol_table = SymbolTable()
        
        # Add local symbols
        symbol_table.add_symbol("my_project.utils", "file_456")
        symbol_table.add_symbol("my_project.models", "file_789")
        
        # Test prefix matching (e.g., looking for my_project.utils.helper)
        assert (symbol_table.is_local_module("my_project.utils.helper_function") 
                is True)
        assert symbol_table.is_local_module("my_project.models.User") is True
        
        # Should still return False for non-local
        assert symbol_table.is_local_module("fastapi.Request") is False

    def test_is_local_module_parent_match(self):
        """Test local module detection with parent module matching."""
        symbol_table = SymbolTable()
        
        # Add some nested local symbols
        symbol_table.add_symbol("my_project.auth.handlers", "file_123")
        symbol_table.add_symbol("my_project.db.models", "file_456")
        
        # These should be detected as local because they have children
        assert symbol_table.is_local_module("my_project.auth") is True
        assert symbol_table.is_local_module("my_project.db") is True
        assert symbol_table.is_local_module("my_project") is True

    def test_get_or_create_package_id(self):
        """Test package ID creation and retrieval."""
        symbol_table = SymbolTable()
        
        # Test creating a new package
        package_id = symbol_table.get_or_create_package_id("fastapi")
        assert package_id == "package_fastapi"
        assert symbol_table.get_symbol_id("fastapi") == "package_fastapi"
        
        # Test retrieving existing package
        same_id = symbol_table.get_or_create_package_id("fastapi")
        assert same_id == package_id
        
        # Test package with dots
        numpy_id = symbol_table.get_or_create_package_id("numpy.array")
        assert numpy_id == "package_numpy_array"

    def test_clear_file_imports(self):
        """Test clearing imports for a specific file."""
        symbol_table = SymbolTable()
        
        # Add imports for multiple files
        symbol_table.add_import("file_123", "Request", "fastapi.Request")
        symbol_table.add_import("file_123", "np", "numpy")
        symbol_table.add_import("file_456", "json", "json")
        
        # Clear imports for one file
        symbol_table.clear_file_imports("file_123")
        
        # Check that file_123 imports are cleared
        assert symbol_table.get_file_imports("file_123") == {}
        
        # Check that other file imports remain
        assert symbol_table.get_file_imports("file_456") == {"json": "json"}
        
        # Clearing non-existent file should not raise error
        symbol_table.clear_file_imports("nonexistent")

    def test_get_all_local_modules(self):
        """Test getting all local module names."""
        symbol_table = SymbolTable()
        
        # Initially empty
        assert symbol_table.get_all_local_modules() == []
        
        # Add some symbols
        symbol_table.add_symbol("my_project", "project_123")
        symbol_table.add_symbol("my_project.utils", "file_456")
        symbol_table.add_symbol("my_project.models.user", "file_789")
        
        local_modules = symbol_table.get_all_local_modules()
        assert set(local_modules) == {
            "my_project",
            "my_project.utils", 
            "my_project.models.user"
        }

    def test_integration_scenario(self):
        """Test a realistic integration scenario."""
        symbol_table = SymbolTable()
        
        # Simulate project structure
        symbol_table.add_symbol("my_app", "project_1")
        symbol_table.add_symbol("my_app.main", "file_1")
        symbol_table.add_symbol("my_app.utils", "file_2")
        symbol_table.add_symbol("my_app.models.user", "file_3")
        symbol_table.add_symbol("my_app.api.handlers", "file_4")
        
        # Add imports for main.py
        symbol_table.add_import("file_1", "Request", "fastapi.Request")
        symbol_table.add_import("file_1", "user_utils", "my_app.utils")
        symbol_table.add_import("file_1", "User", "my_app.models.user.User")
        
        # Test resolution
        assert symbol_table.resolve_import_qname("file_1", "Request") == "fastapi.Request"
        assert symbol_table.resolve_import_qname("file_1", "user_utils") == "my_app.utils"
        assert symbol_table.resolve_import_qname("file_1", "User") == "my_app.models.user.User"
        
        # Test local vs external detection
        assert symbol_table.is_local_module("fastapi.Request") is False
        assert symbol_table.is_local_module("my_app.utils") is True
        assert symbol_table.is_local_module("my_app.models.user.User") is True
        
        # Test package creation for external dependencies
        fastapi_id = symbol_table.get_or_create_package_id("fastapi")
        assert fastapi_id == "package_fastapi"

    def test_scope_stack_operations(self):
        """Test scope stack operations (Phase 4 preparation)."""
        symbol_table = SymbolTable()
        
        # Initially empty stack
        assert symbol_table.pop_scope() is None
        
        # Push scopes
        symbol_table.push_scope("function_1")
        symbol_table.push_scope("function_2")
        symbol_table.push_scope("function_3")
        
        # Pop scopes in LIFO order
        assert symbol_table.pop_scope() == "function_3"
        assert symbol_table.pop_scope() == "function_2"
        assert symbol_table.pop_scope() == "function_1"
        assert symbol_table.pop_scope() is None 