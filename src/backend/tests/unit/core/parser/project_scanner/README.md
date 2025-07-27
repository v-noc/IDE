# Project Scanner Tests

This directory contains modularized tests for the ProjectScanner functionality, organized by concern for better maintainability and readability.

## Test Organization

### Core Test Files

- **`test_basic_scanning.py`** - Basic project scanning functionality
  - Declaration pass tests
  - Node creation verification
  - Package node creation
  - Scan summary validation

- **`test_project_structure.py`** - Project structure and hierarchy tests
  - Tree structure validation
  - Nested folder handling
  - File and folder detection
  - Class inheritance and enum detection

- **`test_import_analysis.py`** - Import analysis and resolution
  - Import position tracking
  - Aliased imports (import X as Y)
  - Relative imports (from . import)
  - Import position accuracy

- **`test_qname_resolution.py`** - Qualified name resolution and path mapping
  - QName to path mapping
  - Simple and nested module resolution
  - QName uniqueness validation
  - Package QName resolution

- **`test_error_handling.py`** - Error handling and edge cases
  - Import error resilience
  - Circular import handling
  - Missing import scenarios
  - Large file processing

- **`test_complex_project.py`** - Complex project specific tests
  - Comprehensive structure analysis
  - Service and model layer validation
  - External dependency handling
  - Multi-layer architecture testing

### Supporting Files

- **`conftest.py`** - Shared fixtures and utilities
  - `sample_project_path` - Path to simple test project
  - `complex_project_path` - Path to complex test project
  - `scanner_test_utils` - Helper functions for testing

- **`__init__.py`** - Package initialization

## Test Projects

### Sample Project
Located at `../sample_project/` - A simple project with basic structure:
- `main.py` - Main application file
- `utils.py` - Utility functions
- `models/user.py` - User model
- `models/__init__.py` - Package init

### Complex Project  
Located at `../complex_project/` - A comprehensive project with:
- Nested folder structure (`services/data/`)
- Various import patterns (absolute, relative, aliased)
- Multiple layers (models, services, utils)
- Complex inheritance hierarchies
- External dependencies

## Running Tests

### Run all scanner tests:
```bash
pytest tests/unit/core/parser/project_scanner/ -v
```

### Run specific test categories:
```bash
# Basic functionality
pytest tests/unit/core/parser/project_scanner/test_basic_scanning.py -v

# Import analysis
pytest tests/unit/core/parser/project_scanner/test_import_analysis.py -v

# Structure tests
pytest tests/unit/core/parser/project_scanner/test_project_structure.py -v

# QName resolution
pytest tests/unit/core/parser/project_scanner/test_qname_resolution.py -v

# Error handling
pytest tests/unit/core/parser/project_scanner/test_error_handling.py -v

# Complex scenarios
pytest tests/unit/core/parser/project_scanner/test_complex_project.py -v
```

## Test Utilities

The `scanner_test_utils` fixture provides helper methods:
- `count_nodes_by_type(nodes, node_type)` - Count nodes of specific type
- `find_node_by_qname(nodes, qname)` - Find node by qualified name
- `get_import_edges_by_target(edges, pattern)` - Filter import edges

## Benefits of This Structure

1. **Maintainability** - Each file focuses on a specific aspect
2. **Readability** - Easier to find and understand tests
3. **Parallel Testing** - Tests can run in parallel more efficiently
4. **Focused Debugging** - Easier to isolate and debug specific issues
5. **Scalability** - Easy to add new test categories as needed

## Adding New Tests

When adding new tests:
1. Choose the appropriate category file or create a new one
2. Use the shared fixtures from `conftest.py`
3. Follow the existing naming conventions
4. Include descriptive docstrings
5. Update this README if adding new categories 