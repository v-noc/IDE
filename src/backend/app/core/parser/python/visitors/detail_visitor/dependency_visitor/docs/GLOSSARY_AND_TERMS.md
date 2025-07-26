# Dependency Visitor Glossary & Terms

## Table of Contents
- [Core Concepts](#core-concepts)
- [Technical Terms](#technical-terms)
- [Variable Names & Conventions](#variable-names--conventions)
- [Data Structures](#data-structures)
- [Algorithm Terms](#algorithm-terms)
- [System Components](#system-components)

## Core Concepts

### **Dependency**
A relationship where one code element (consumer) uses functionality from another code element (provider). In Python, this typically manifests as import usage.

**Example:**
```python
import json          # Creates dependency relationship
json.loads("{}")     # Usage of the dependency
```

### **Import Resolution**
The process of converting import statements and their usage into fully qualified names that can be tracked and analyzed.

**Example:**
```python
from os import path as p    # Import statement
p.join("a", "b")           # Usage → resolves to "os.path.join"
```

### **Consumer**
The code element (function, class, or method) that uses an imported symbol. This becomes the `_from` side of a dependency edge.

**Example:**
```python
def my_function():    # <- Consumer
    json.loads("{}")  # Usage within consumer context
```

### **Provider/Target**
The imported symbol or module being used. This becomes the `_to` side of a dependency edge.

**Example:**
```python
import json
json.loads("{}")  # json.loads is the provider/target
```

### **Symbol Table**
A central registry that maps names to their fully qualified names and database IDs, enabling resolution of imports and local symbols.

### **QName (Qualified Name)**
A fully qualified name that uniquely identifies a symbol within the project namespace.

**Examples:**
- File: `myproject.utils.helpers`
- Function: `myproject.utils.helpers.process_data`
- Import: `numpy.array`

---

## Technical Terms

### **AST (Abstract Syntax Tree)**
Python's parsed representation of source code as a tree structure, where each node represents a language construct.

**Relevant AST Node Types:**
- `ast.Import`: Regular import statements
- `ast.ImportFrom`: From-import statements  
- `ast.Name`: Variable/function name references
- `ast.Attribute`: Attribute access (e.g., `obj.attr`)
- `ast.FunctionDef`: Function definitions
- `ast.ClassDef`: Class definitions

### **Visitor Pattern**
A design pattern used to traverse AST nodes, where each node type has a corresponding `visit_*` method.

**Example:**
```python
def visit_Import(self, node: ast.Import):
    # Process import statement
    pass
```

### **Context Management**
The system for tracking which function or class is currently being analyzed, ensuring dependency edges are attributed correctly.

### **Edge Creation**
The process of creating `UsesImportEdge` objects that represent dependency relationships in the graph database.

### **Relative Import Resolution**
Converting relative imports (with dots) to absolute qualified names based on the current file's location in the package hierarchy.

**Example:**
```python
# In file: myproject.services.api
from ..utils import helper    # Resolves to: myproject.utils.helper
from . import config          # Resolves to: myproject.services.config
```

### **Wildcard Import**
An import statement that imports all public symbols from a module using the `*` syntax. Currently has **limited support** in the dependency visitor.

**Example:**
```python
from pathlib import *    # Wildcard import - symbols not tracked
from os import path      # Explicit import - symbols tracked
```

**Limitation:** Wildcard imports are recorded but individual symbols are not registered in the symbol table, so usage of those symbols won't create dependency edges.

---

## Variable Names & Conventions

### **Common Variable Names**

#### `context` (`VisitorContext`)
The shared state object passed between all visitor components, containing:
- `file_id`: Database ID of current file
- `ast`: Parsed AST tree  
- `symbol_table`: Symbol resolution engine
- `results`: Output collection for edges

#### `node` (`ast.AST`)
The current AST node being processed by a visitor method.

#### `qname` (`str`)
Qualified name - the full dotted path to identify a symbol.
```python
qname = "myproject.utils.helpers.process_data"
```

#### `alias` (`str`)
The name used to refer to an import in the code (considering `as` clauses).
```python
import numpy as np  # alias = "np"
from os import path # alias = "path"
```

#### `target_qname` (`str`)
The fully qualified name of the symbol being used/imported.
```python
# After: import numpy as np
# Usage: np.array([1,2,3])
# target_qname = "numpy.array"
```

#### `target_symbol` (`str`)
The specific symbol name being accessed.
```python
# Usage: np.array([1,2,3])
# target_symbol = "array"
```

#### `consumer_id` (`str`)
Database ID of the function/class/method that is using an import.

#### `file_id` (`str`)
Database ID of the file being analyzed.

### **Instance Variables**

#### In `DependencyVisitor`:
- `context`: Shared visitor context
- `import_processor`: Component for processing imports
- `context_manager`: Component for tracking analysis context
- `usage_detector`: Component for detecting symbol usage

#### In `ImportProcessor`:
- `context`: Shared visitor context
- `processed_imports`: List of processed import AST nodes

#### In `DependencyContextManager`:
- `context`: Shared visitor context
- `current_consumer_id`: Database ID of current function/class being analyzed

#### In `UsageDetector`:
- `context`: Shared visitor context
- `get_current_consumer_id`: Callback function to get current consumer
- `get_processed_imports`: Callback function to get processed imports

### **Method Parameter Conventions**

#### `node` - AST Node Parameters
```python
def visit_Import(self, node: ast.Import) -> None:
def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
def process_import_from(self, node: ast.ImportFrom) -> None:
```

#### `visit_body_callback` - Callback Functions
```python
def visit_function_def(self, node: ast.FunctionDef, visit_body_callback: Callable[[ast.AST], None]) -> None:
```

#### Context and State Parameters
```python
def create_usage_edge(context: VisitorContext, current_consumer_id: str, ...):
def get_relative_import_base(context: VisitorContext, level: int) -> str:
```

---

## Data Structures

### **VisitorContext**
```python
class VisitorContext:
    file_id: str              # Database ID of current file
    ast: ast.Module           # Parsed AST tree
    symbol_table: SymbolTable # Symbol resolution engine  
    results: List[BaseEdge]   # Output collection for all edges
```

### **UsesImportEdge**
```python
class UsesImportEdge(BaseEdge):
    edge_type: str = "uses_import"
    target_symbol: str                 # Specific symbol used
    alias: str | None                  # Alias used in code
    import_position: NodePosition      # Where import statement appears
    usage_positions: List[NodePosition] # Where symbol is used
    
    # Extended attributes:
    target_qname: str                  # Full qualified name for resolution
```

### **NodePosition**
```python
class NodePosition:
    line_no: int              # Starting line number (1-based)
    col_offset: int           # Starting column offset (0-based)
    end_line_no: int          # Ending line number
    end_col_offset: int       # Ending column offset
```

### **SymbolTable Internal Structures**
```python
class SymbolTable:
    _qname_to_id: Dict[str, str]                    # qname → database_id mapping
    _file_id_to_imports: Dict[str, Dict[str, str]]  # file_id → {alias → qname} mapping
    _scope_stack: List[str]                         # Scope tracking stack
```

**Structure Example:**
```python
_qname_to_id = {
    "myproject.utils.helpers": "file_123",
    "myproject.utils.helpers.process_data": "func_456"
}

_file_id_to_imports = {
    "file_123": {
        "json": "json",           # import json
        "np": "numpy",            # import numpy as np
        "Request": "fastapi.Request"  # from fastapi import Request
    }
}
```

---

## Algorithm Terms

### **Attribute Chain Reconstruction**
The process of parsing complex attribute access expressions to extract the base name and full access path.

**Algorithm Example:**
```python
# Expression: np.random.seed(42)
# Chain: ["np", "random", "seed"]
# Base: "np" (resolved to "numpy")
# Result: "numpy.random.seed"
```

### **Context Stack Management**
Tracking nested scopes (functions within classes, nested functions) to maintain proper consumer context.

**Example:**
```python
class DataProcessor:           # Context: class_id_123
    def process(self):         # Context: method_id_456 (nested)
        def helper():          # Context: func_id_789 (doubly nested)
            import json        # Consumer: func_id_789
```

### **Two-Phase Resolution**
The dependency visitor uses a two-phase approach:

1. **Phase 1 (Local Resolution)**: Resolve imports to qualified names, create edges with known consumers
2. **Phase 2 (External Resolution)**: Scanner resolves target qualified names to actual database IDs

### **Import Position Finding**
Algorithm to locate the original import statement that introduced a given alias.

**Search Process:**
1. Iterate through all processed import nodes
2. Check each alias in each import
3. Match alias name (considering `asname`)
4. Return position of matching import

---

## System Components

### **Primary Components**

#### **DependencyVisitor**
- **Role**: Main orchestrator implementing `ast.NodeVisitor`
- **Responsibility**: Coordinates all specialized components
- **Key Methods**: `visit_*` methods for each AST node type

#### **ImportProcessor** 
- **Role**: Import statement specialist
- **Responsibility**: Processes `import` and `from...import` statements
- **Key Methods**: `process_import()`, `process_import_from()`

#### **DependencyContextManager**
- **Role**: Context tracking specialist  
- **Responsibility**: Manages which function/class is currently being analyzed
- **Key Methods**: `visit_function_def()`, `visit_class_def()`, `get_current_consumer_id()`

#### **UsageDetector**
- **Role**: Symbol usage detection specialist
- **Responsibility**: Finds where imported symbols are used and creates edges
- **Key Methods**: `detect_name_usage()`, `detect_attribute_usage()`

### **Helper Functions**

#### **`get_file_qname_from_context()`**
Extracts the current file's qualified name from the visitor context.

#### **`get_relative_import_base()`**  
Calculates the base module for relative imports based on dot level.

#### **`reconstruct_attribute_chain()`**
Parses attribute access expressions into component parts.

#### **`create_usage_edge()`**
Creates and stores `UsesImportEdge` objects in the results collection.

#### **`find_import_position()`**
Locates the import statement that introduced a specific alias.

### **Integration Components**

#### **SymbolTable**
- **Provider**: Symbol resolution services
- **Interface**: `add_import()`, `resolve_import_qname()`, `is_local_module()`

#### **VisitorContext**
- **Provider**: Shared state management
- **Contents**: File ID, AST tree, symbol table, results collection

#### **Project Scanner**
- **Consumer**: Uses dependency visitor as part of file analysis pipeline
- **Role**: Orchestrates visitor execution and result aggregation

---

## Naming Patterns & Standards

### **Method Naming**
- `visit_*`: AST visitor methods (e.g., `visit_Import`, `visit_Name`)
- `process_*`: Processing methods (e.g., `process_import`)
- `detect_*`: Detection methods (e.g., `detect_name_usage`)
- `get_*`: Getter methods (e.g., `get_current_consumer_id`)
- `create_*`: Factory methods (e.g., `create_usage_edge`)

### **File Naming**
- `__init__.py`: Main orchestrator class
- `*_processor.py`: Specialized processing components
- `*_manager.py`: State management components  
- `*_detector.py`: Detection/analysis components
- `helpers.py`: Utility functions

### **Variable Naming Patterns**
- `*_id`: Database identifiers (e.g., `consumer_id`, `file_id`)
- `*_qname`: Qualified names (e.g., `target_qname`, `file_qname`)
- `*_position`: Position objects (e.g., `import_position`, `usage_position`)
- `*_node`: AST nodes (e.g., `import_node`, `name_node`)
- `*_callback`: Callback functions (e.g., `visit_body_callback`)

### **Constant Naming**
- `MAX_*`: Limits and thresholds
- `DEFAULT_*`: Default values
- `*_TYPE`: Type identifiers

This glossary provides comprehensive coverage of all terms, variables, and concepts used throughout the dependency visitor system. 