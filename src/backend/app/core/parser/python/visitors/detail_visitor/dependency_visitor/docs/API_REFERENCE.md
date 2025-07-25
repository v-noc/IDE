# Dependency Visitor API Reference

## Table of Contents
- [DependencyVisitor (Main Class)](#dependencyvisitor-main-class)
- [ImportProcessor](#importprocessor)
- [DependencyContextManager](#dependencycontextmanager)
- [UsageDetector](#usagedetector)
- [Helper Functions](#helper-functions)
- [Data Models](#data-models)

---

## DependencyVisitor (Main Class)

**Location**: `dependency_visitor/__init__.py`

### Class: `DependencyVisitor(ast.NodeVisitor)`

Main orchestrator class that coordinates all dependency analysis components.

#### Constructor

```python
def __init__(self, context: VisitorContext)
```

**Parameters:**
- `context` (`VisitorContext`): Shared context containing file_id, AST tree, symbol table, and results list

**Initialization:**
- Creates `ImportProcessor` instance
- Creates `DependencyContextManager` instance  
- Creates `UsageDetector` instance with callback functions
- Establishes component communication channels

#### Core AST Visitor Methods

##### `visit_FunctionDef(self, node: ast.FunctionDef) -> None`

Sets analysis context for function definitions.

**Parameters:**
- `node` (`ast.FunctionDef`): Function definition AST node

**Behavior:**
1. Delegates to `context_manager.visit_function_def()`
2. Establishes function as current consumer
3. Visits function body with proper context
4. Restores previous context after processing

**Usage Example:**
```python
# Automatically called when AST contains:
def my_function():
    import json  # Will be processed in function context
    json.loads("{}")  # Usage tracked to my_function
```

##### `visit_ClassDef(self, node: ast.ClassDef) -> None`

Sets analysis context for class definitions.

**Parameters:**
- `node` (`ast.ClassDef`): Class definition AST node

**Behavior:**  
1. Delegates to `context_manager.visit_class_def()`
2. Establishes class as current consumer
3. Visits class body with proper context
4. Restores previous context after processing

##### `visit_Import(self, node: ast.Import) -> None`

Processes regular import statements.

**Parameters:**
- `node` (`ast.Import`): Import statement AST node

**Examples Handled:**
```python
import os                    # os → os
import numpy as np          # np → numpy  
import json, sys            # json → json, sys → sys
```

##### `visit_ImportFrom(self, node: ast.ImportFrom) -> None`

Processes from-import statements.

**Parameters:**
- `node` (`ast.ImportFrom`): From-import statement AST node

**Examples Handled:**
```python
from os import path                    # path → os.path
from json import loads as json_loads   # json_loads → json.loads
from .utils import helper              # helper → resolved.absolute.qname
from .. import parent_module           # parent_module → resolved.parent.qname
```

##### `visit_Name(self, node: ast.Name) -> None`

Handles usage of simple imported names.

**Parameters:**
- `node` (`ast.Name`): Name reference AST node

**Examples Handled:**
```python
# After: from fastapi import Request
Request()  # Tracked as usage of fastapi.Request
```

##### `visit_Attribute(self, node: ast.Attribute) -> None`

Handles usage of attribute access on imported names.

**Parameters:**
- `node` (`ast.Attribute`): Attribute access AST node

**Examples Handled:**
```python
# After: import numpy as np
np.array([1, 2, 3])        # Tracked as usage of numpy.array
np.random.seed(42)         # Tracked as usage of numpy.random.seed
```

#### Analysis Method

##### `get_analysis_summary(self) -> dict`

Returns comprehensive analysis statistics.

**Returns:** Dictionary with structure:
```python
{
    "total_imports_processed": int,
    "import_types": {
        "regular_imports": int,      # Count of 'import' statements
        "from_imports": int          # Count of 'from...import' statements  
    },
    "has_active_consumer": bool,     # Whether in function/class context
    "total_edges_created": int       # Number of UsesImportEdge objects
}
```

---

## ImportProcessor

**Location**: `dependency_visitor/import_processor.py`

### Class: `ImportProcessor`

Specialized component for processing Python import statements.

#### Constructor

```python
def __init__(self, context: VisitorContext)
```

**Instance Variables:**
- `context` (`VisitorContext`): Shared analysis context
- `processed_imports` (`List[Union[ast.Import, ast.ImportFrom]]`): Registry of processed imports

#### Methods

##### `process_import(self, node: ast.Import) -> None`

Processes regular import statements and registers them in symbol table.

**Parameters:**
- `node` (`ast.Import`): Import AST node to process

**Processing Logic:**
1. Adds node to `processed_imports` registry
2. Extracts each alias from `node.names`
3. Determines alias name (uses `asname` if present, otherwise `name`)
4. Calls `symbol_table.add_import(file_id, alias, qname)`

**Examples:**
```python
# import os
# Results in: symbol_table.add_import(file_id, "os", "os")

# import numpy as np  
# Results in: symbol_table.add_import(file_id, "np", "numpy")
```

##### `process_import_from(self, node: ast.ImportFrom) -> None`

Processes from-import statements with full qname resolution.

**Parameters:**
- `node` (`ast.ImportFrom`): ImportFrom AST node to process

**Processing Logic:**
1. Adds node to `processed_imports` registry
2. Handles relative imports using `get_relative_import_base()`
3. Constructs full qname: `{base_module}.{symbol_name}`
4. Registers each non-wildcard import in symbol table
5. Handles aliases properly

**Special Cases:**
- **Relative imports**: `from .utils import helper` → resolved using file context
- **Wildcard imports**: `from module import *` → logged but not processed
- **No module**: `from . import something` → uses relative resolution

##### `get_processed_imports(self) -> List[Union[ast.Import, ast.ImportFrom]]`

Returns list of all processed import nodes for reference by other components.

---

## DependencyContextManager

**Location**: `dependency_visitor/context_manager.py`

### Class: `DependencyContextManager`

Manages analysis context to track which function or class is currently being analyzed.

#### Constructor

```python
def __init__(self, context: VisitorContext)
```

**Instance Variables:**
- `context` (`VisitorContext`): Shared analysis context
- `current_consumer_id` (`Optional[str]`): Database ID of current function/class being analyzed

#### Methods

##### `visit_function_def(self, node: ast.FunctionDef, visit_body_callback: Callable[[ast.AST], None]) -> None`

Establishes function context for dependency analysis.

**Parameters:**
- `node` (`ast.FunctionDef`): Function definition node
- `visit_body_callback` (`Callable`): Callback to visit function body (usually `self.generic_visit`)

**Processing Steps:**
1. Constructs function qname: `{file_qname}.{function_name}`
2. Looks up function's database ID from symbol table
3. Sets `current_consumer_id` to function's ID
4. Invokes callback to visit function body
5. Restores previous consumer context

**Context Handling:**
```python
# Before: current_consumer_id = None
def my_function():
    # Inside: current_consumer_id = "function_db_id_123"
    import json
    json.loads("{}")  # Tracked with consumer = "function_db_id_123"
# After: current_consumer_id = None (restored)
```

##### `visit_class_def(self, node: ast.ClassDef, visit_body_callback: Callable[[ast.AST], None]) -> None`

Establishes class context for dependency analysis.

**Parameters:**
- `node` (`ast.ClassDef`): Class definition node  
- `visit_body_callback` (`Callable`): Callback to visit class body

**Processing Steps:**
1. Constructs class qname: `{file_qname}.{class_name}`
2. Looks up class's database ID from symbol table
3. Sets `current_consumer_id` to class's ID
4. Invokes callback to visit class body
5. Restores previous consumer context

##### `get_current_consumer_id(self) -> Optional[str]`

Returns the database ID of the function or class currently being analyzed.

**Returns:** Database ID string or `None` if no active context

##### `has_current_consumer(self) -> bool`

Checks if there is an active consumer context.

**Returns:** `True` if analysis is within a function/class, `False` otherwise

---

## UsageDetector

**Location**: `dependency_visitor/usage_detector.py`

### Class: `UsageDetector`

Detects usage of imported symbols and creates dependency edges.

#### Constructor

```python
def __init__(
    self, 
    context: VisitorContext, 
    get_current_consumer_id_func,
    get_processed_imports_func
)
```

**Parameters:**
- `context` (`VisitorContext`): Shared analysis context
- `get_current_consumer_id_func` (`Callable`): Function to get current consumer ID
- `get_processed_imports_func` (`Callable`): Function to get processed imports list

#### Methods

##### `detect_name_usage(self, node: ast.Name) -> None`

Detects usage of simple imported names.

**Parameters:**
- `node` (`ast.Name`): Name reference AST node

**Processing Logic:**
1. Checks if there's an active consumer context
2. Verifies node is in Load context (not Store/Del)
3. Attempts to resolve name through `symbol_table.resolve_import_qname()`
4. If resolved, creates `UsesImportEdge` via `create_usage_edge()`

**Example Flow:**
```python
# After import: from fastapi import Request
# Code: Request()
# 1. node.id = "Request"
# 2. resolved_qname = "fastapi.Request" 
# 3. Creates edge: consumer → fastapi.Request
```

##### `detect_attribute_usage(self, node: ast.Attribute, visit_callback) -> None`

Detects usage of attribute access chains on imported names.

**Parameters:**
- `node` (`ast.Attribute`): Attribute access AST node
- `visit_callback` (`Callable`): Callback to continue AST traversal

**Processing Logic:**
1. Reconstructs full attribute chain using `reconstruct_attribute_chain()`
2. Identifies base name (first element in chain)
3. Attempts to resolve base name through symbol table
4. Constructs full target qname by combining resolved base with attribute chain
5. Creates `UsesImportEdge` for the usage

**Example Flow:**
```python
# After import: import numpy as np
# Code: np.random.seed(42)
# 1. chain = ["np", "random", "seed"]
# 2. base = "np", resolved = "numpy"
# 3. full_target = "numpy.random.seed"
# 4. Creates edge: consumer → numpy.random.seed
```

---

## Helper Functions

**Location**: `dependency_visitor/helpers.py`

### Core Utility Functions

#### `get_file_qname_from_context(context: VisitorContext) -> str`

Extracts the file's qualified name from the visitor context.

**Parameters:**
- `context` (`VisitorContext`): Current analysis context

**Returns:** File's qname string

**Logic:**
1. Searches symbol table's `_qname_to_id` mapping
2. Finds entry where node_id matches `context.file_id`
3. Returns corresponding qname
4. Fallbacks to "unknown_file" if not found

#### `get_relative_import_base(context: VisitorContext, level: int) -> str`

Calculates base module for relative imports.

**Parameters:**
- `context` (`VisitorContext`): Current analysis context
- `level` (`int`): Number of dots in relative import

**Returns:** Base module name for relative import

**Logic:**
1. Gets current file's qname
2. Splits into components by '.'
3. Removes `level` components from the end
4. Rejoins remaining components

**Examples:**
```python
# File: myproject.utils.helpers
# level=1 (from . import): returns "myproject.utils"
# level=2 (from .. import): returns "myproject"
```

#### `reconstruct_attribute_chain(node: ast.Attribute) -> List[str]`

Reconstructs full attribute access chain from AST node.

**Parameters:**
- `node` (`ast.Attribute`): Attribute access AST node

**Returns:** List of names in the chain, empty list if complex

**Examples:**
```python
# np.array → ["np", "array"]
# requests.get().json() → [] (complex, can't resolve)
# a.b.c.d → ["a", "b", "c", "d"]
```

**Algorithm:**
1. Start with attribute name (`node.attr`)
2. Walk up the value chain
3. If `ast.Attribute`, add to front of chain
4. If `ast.Name`, add to front and return
5. If complex expression, return empty list

#### `create_usage_edge(...) -> None`

Creates a `UsesImportEdge` object and adds it to results.

**Parameters:**
- `context` (`VisitorContext`): Analysis context
- `current_consumer_id` (`str`): Consumer's database ID
- `processed_imports` (`List`): List of processed import nodes
- `target_qname` (`str`): Fully qualified target name
- `target_symbol` (`str`): Specific symbol being used
- `alias` (`str`): Alias used in code
- `usage_position` (`NodePosition`): Position of usage

**Processing:**
1. Finds import position using `find_import_position()`
2. Creates `UsesImportEdge` object with all parameters
3. Adds custom `target_qname` attribute for scanner processing
4. Appends edge to `context.results`

#### `find_import_position(processed_imports: List, alias: str) -> Optional[NodePosition]`

Locates the import statement that introduced a given alias.

**Parameters:**
- `processed_imports` (`List`): Processed import AST nodes
- `alias` (`str`): Alias to search for

**Returns:** `NodePosition` of import statement or `None`

**Search Logic:**
1. Iterates through all processed imports
2. For each import, checks all aliases
3. Compares used name (considering `asname`) with target alias
4. Returns position of matching import statement

---

## Data Models

### VisitorContext

**Location**: `visitor_context.py`

```python
class VisitorContext:
    file_id: str           # Database ID of current file
    ast: ast.Module        # Parsed AST tree
    symbol_table: SymbolTable  # Symbol resolution engine
    results: List          # Output collection for edges
```

### UsesImportEdge

**Location**: `app/models/edges.py`

```python
class UsesImportEdge(BaseEdge):
    edge_type: str = "uses_import"
    target_symbol: str           # Specific symbol (e.g., 'Request')
    alias: str | None           # Alias used (e.g., 'np')
    import_position: NodePosition    # Where import appears
    usage_positions: List[NodePosition]  # Where symbol is used
    
    # Custom attributes added by dependency visitor:
    target_qname: str           # Full qualified name for resolution
```

### NodePosition

```python
class NodePosition:
    line_no: int              # Starting line number
    col_offset: int           # Starting column offset  
    end_line_no: int          # Ending line number
    end_col_offset: int       # Ending column offset
```

This API reference covers all public interfaces and internal implementation details of the dependency visitor system. 