# Modular Dependency Visitor

This directory contains the refactored dependency visitor components, split from the original monolithic `dependecy_visitor.py` file for better maintainability and separation of concerns.

## Structure

```
dependency_visitor/
├── __init__.py              # Main DependencyVisitor orchestrator
├── helpers.py               # Utility functions
├── import_processor.py      # Import statement processing
├── context_manager.py       # Function/class context management  
├── usage_detector.py        # Symbol usage detection
└── README.md               # This documentation
```

## Components

### 1. `__init__.py` - Main Orchestrator
The main `DependencyVisitor` class that coordinates all components:
- Inherits from `ast.NodeVisitor`
- Delegates to specialized components
- Maintains the same public API as the original
- Provides analysis summary functionality

### 2. `helpers.py` - Utility Functions
Common utility functions used across components:
- `get_file_qname_from_context()` - Extract file qname from context
- `get_relative_import_base()` - Calculate relative import base
- `reconstruct_attribute_chain()` - Parse attribute access chains
- `create_usage_edge()` - Create UsesImportEdge models
- `find_import_position()` - Locate import statement positions

### 3. `import_processor.py` - Import Processing
Handles import statement processing:
- `ImportProcessor` class
- Processes `import` and `from...import` statements
- Handles relative imports and aliases
- Registers imports in the symbol table

### 4. `context_manager.py` - Context Management
Manages function and class analysis context:
- `DependencyContextManager` class  
- Tracks current consumer (function/class being analyzed)
- Provides proper context for dependency edges
- Handles nested contexts correctly

### 5. `usage_detector.py` - Usage Detection
Detects symbol usage in code:
- `UsageDetector` class
- Handles simple name references (`json`)
- Handles complex attribute access (`np.array`)
- Creates dependency edges for detected usage

## Usage

The refactored components maintain full backward compatibility:

```python
from .dependency_visitor import DependencyVisitor

# Usage remains exactly the same
visitor = DependencyVisitor(context)
visitor.visit(ast_tree)

# New: Get analysis summary
summary = visitor.get_analysis_summary()
```

## Benefits

1. **Single Responsibility**: Each component has a focused purpose
2. **Testability**: Components can be tested independently  
3. **Maintainability**: Easier to modify individual aspects
4. **Readability**: Smaller, focused files are easier to understand
5. **Extensibility**: Easy to add new components or modify existing ones

## Migration

- No changes required for existing code
- All imports continue to work (`from .dependency_visitor import DependencyVisitor`)
- Same API and functionality as the original monolithic version
- Tests pass without modification 