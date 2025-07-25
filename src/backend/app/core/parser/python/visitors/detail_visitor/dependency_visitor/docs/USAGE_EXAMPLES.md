# Dependency Visitor Usage Examples & Troubleshooting

## Table of Contents
- [Basic Usage Examples](#basic-usage-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Common Patterns](#common-patterns)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Performance Considerations](#performance-considerations)
- [Testing Strategies](#testing-strategies)

## Basic Usage Examples

### Simple Import Analysis

```python
# sample_file.py
import json
import numpy as np
from fastapi import Request
from .utils import helper

def process_data(data):
    parsed = json.loads(data)
    array = np.array(parsed)
    return helper(array)

class DataProcessor:
    def handle_request(self, request: Request):
        return json.dumps({"status": "ok"})
```

**Expected Dependency Edges:**

```python
# From process_data function:
UsesImportEdge(
    _from="function_process_data_id",
    target_qname="json.loads",
    target_symbol="loads", 
    alias="json",
    usage_positions=[line 7]
)

UsesImportEdge(
    _from="function_process_data_id", 
    target_qname="numpy.array",
    target_symbol="array",
    alias="np",
    usage_positions=[line 8]
)

UsesImportEdge(
    _from="function_process_data_id",
    target_qname="myproject.utils.helper", 
    target_symbol="helper",
    alias="helper",
    usage_positions=[line 9]
)

# From DataProcessor.handle_request method:
UsesImportEdge(
    _from="method_handle_request_id",
    target_qname="json.dumps",
    target_symbol="dumps",
    alias="json", 
    usage_positions=[line 13]
)
```

### Usage with Context

```python
# Creating and using the dependency visitor
from ..visitor_context import VisitorContext
from .dependency_visitor import DependencyVisitor

# Setup context (normally done by file parser)
context = VisitorContext(
    file_id="file_123",
    ast=ast_tree, 
    symbol_table=populated_symbol_table
)

# Create and run visitor
visitor = DependencyVisitor(context)
visitor.visit(ast_tree)

# Access results
dependency_edges = [
    edge for edge in context.results 
    if isinstance(edge, UsesImportEdge)
]

# Get analysis summary
summary = visitor.get_analysis_summary()
print(f"Processed {summary['total_imports_processed']} imports")
print(f"Created {summary['total_edges_created']} dependency edges")
```

## Advanced Scenarios

### Complex Attribute Chains

```python
# complex_usage.py
import requests
import numpy as np
from sklearn.model_selection import train_test_split

def analyze_data():
    # Simple attribute access
    response = requests.get("http://api.example.com")
    data = response.json()
    
    # Complex chain resolution
    random_state = np.random.RandomState(42)
    samples = random_state.normal(0, 1, 1000)
    
    # Direct function usage
    X_train, X_test = train_test_split(samples, test_size=0.2)
    
    return X_train, X_test
```

**Dependency Resolution:**

```python
# requests.get -> tracks "requests.get" usage
UsesImportEdge(target_qname="requests.get", alias="requests")

# response.json() -> NOT tracked (method on returned object)
# This is intentional - we only track direct imported symbol usage

# np.random.RandomState -> tracks "numpy.random.RandomState" 
UsesImportEdge(target_qname="numpy.random.RandomState", alias="np")

# random_state.normal() -> NOT tracked (method on instance)

# train_test_split -> tracks direct usage
UsesImportEdge(target_qname="sklearn.model_selection.train_test_split", alias="train_test_split")
```

### Relative Import Handling

```python
# Directory structure:
# myproject/
#   ├── __init__.py
#   ├── utils/
#   │   ├── __init__.py  
#   │   ├── helpers.py
#   │   └── validators.py
#   └── services/
#       ├── __init__.py
#       └── data_service.py

# File: myproject/services/data_service.py
from ..utils import helpers
from ..utils.validators import validate_input  
from ..__init__ import PROJECT_CONFIG
from . import __init__ as service_init

def process_request(data):
    if validate_input(data):
        return helpers.process(data, PROJECT_CONFIG)
    return service_init.DEFAULT_RESPONSE
```

**Relative Import Resolution:**

```python
# from ..utils import helpers
# Level 2: myproject.services -> myproject
# Base: myproject + utils = myproject.utils
# Target: myproject.utils.helpers
UsesImportEdge(target_qname="myproject.utils.helpers", alias="helpers")

# from ..utils.validators import validate_input
# Level 2: myproject.services -> myproject  
# Base: myproject.utils.validators
# Target: myproject.utils.validators.validate_input
UsesImportEdge(target_qname="myproject.utils.validators.validate_input", alias="validate_input")

# from ..__init__ import PROJECT_CONFIG
# Level 2: myproject.services -> myproject
# Base: myproject
# Target: myproject.PROJECT_CONFIG
UsesImportEdge(target_qname="myproject.PROJECT_CONFIG", alias="PROJECT_CONFIG")
```

### Nested Context Handling

```python
# nested_context.py
import json
from typing import Dict, List

class DataProcessor:
    def __init__(self):
        # Usage in class context (not method)
        self.config = json.loads('{"default": true}')
    
    def process_batch(self, items: List[Dict]):
        # Usage in method context
        results = []
        for item in items:
            processed = json.dumps(item)
            results.append(processed)
        return results
    
    class NestedProcessor:
        def nested_method(self):
            # Usage in nested class method
            return json.loads('{"nested": true}')
```

**Context Resolution:**

```python
# Class-level usage (DataProcessor.__init__)
UsesImportEdge(
    _from="class_DataProcessor_id",  # Class as consumer
    target_qname="json.loads"
)

# Method-level usage (DataProcessor.process_batch)  
UsesImportEdge(
    _from="method_process_batch_id",  # Method as consumer
    target_qname="json.dumps"
)

# Nested class method usage (NestedProcessor.nested_method)
UsesImportEdge(
    _from="method_nested_method_id",  # Nested method as consumer
    target_qname="json.loads"
)
```

## Common Patterns

### Pattern 1: External Library Usage

```python
# external_libs.py
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

def analyze_dataset(data_path):
    # Pandas operations
    df = pd.read_csv(data_path)
    summary = df.describe()
    
    # Matplotlib plotting
    fig, ax = plt.subplots()
    ax.hist(df['value'])
    plt.show()
    
    # Scikit-learn modeling
    model = RandomForestClassifier()
    model.fit(df[['feature']], df['target'])
    
    return model, summary
```

**Generated Edges:**
- `pd.read_csv` → `pandas.read_csv`
- `df.describe()` → NOT tracked (method on DataFrame)
- `plt.subplots` → `matplotlib.pyplot.subplots`
- `plt.show` → `matplotlib.pyplot.show`
- `RandomForestClassifier()` → `sklearn.ensemble.RandomForestClassifier`

### Pattern 2: Local Module Dependencies

```python
# main_service.py
from .database import DatabaseManager
from .utils.logger import setup_logger
from .models.user import User, UserRole
from ..shared.config import settings

class UserService:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = setup_logger(__name__)
    
    def create_user(self, username: str, role: UserRole):
        user = User(username=username, role=role)
        if settings.DEBUG:
            self.logger.info(f"Creating user: {username}")
        return self.db.save(user)
```

**Local Dependencies Tracked:**
- `DatabaseManager` → `myproject.service.database.DatabaseManager`
- `setup_logger` → `myproject.service.utils.logger.setup_logger` 
- `User` → `myproject.service.models.user.User`
- `UserRole` → `myproject.service.models.user.UserRole`
- `settings` → `myproject.shared.config.settings`

### Pattern 3: Import Aliases and Renaming

```python
# aliases.py
import numpy as np
import pandas as pd
from datetime import datetime as dt
from requests import Session as HTTPSession
import json as js

def process_time_series():
    # Aliased imports
    current_time = dt.now()
    data = np.array([1, 2, 3])
    df = pd.DataFrame(data)
    
    # Renamed imports
    http = HTTPSession()
    response_text = js.dumps({"data": data.tolist()})
    
    return df, current_time
```

**Alias Resolution:**
- `dt.now` → `datetime.datetime.now` (alias: `dt`)
- `np.array` → `numpy.array` (alias: `np`)
- `pd.DataFrame` → `pandas.DataFrame` (alias: `pd`)
- `HTTPSession()` → `requests.Session` (alias: `HTTPSession`)
- `js.dumps` → `json.dumps` (alias: `js`)

## Troubleshooting Guide

### Problem 1: Missing Dependency Edges

**Symptoms:**
- Expected edges not appearing in results
- Analysis summary shows 0 edges created

**Diagnosis:**
```python
# Debug the visitor step by step
visitor = DependencyVisitor(context)

# Check if imports are being processed
visitor.visit(ast_tree)
imports = visitor.import_processor.get_processed_imports()
print(f"Processed imports: {len(imports)}")

# Check symbol table state
for file_id, imports in context.symbol_table._file_id_to_imports.items():
    print(f"File {file_id}: {imports}")

# Check current consumer context
summary = visitor.get_analysis_summary()
print(f"Has active consumer: {summary['has_active_consumer']}")
```

**Common Causes & Solutions:**

1. **Declaration Visitor Didn't Run First**
   ```python
   # Problem: No functions/classes in symbol table
   if not context.symbol_table._qname_to_id:
       print("ERROR: Symbol table empty - run DeclarationVisitor first")
   
   # Solution: Ensure proper execution order
   decl_visitor = DeclarationVisitor(context)
   decl_visitor.visit(ast_tree)  # MUST run before DependencyVisitor
   ```

2. **File ID Mismatch**
   ```python
   # Problem: Context file_id doesn't match symbol table entries
   file_imports = context.symbol_table._file_id_to_imports.get(context.file_id)
   if not file_imports:
       print(f"ERROR: No imports for file_id {context.file_id}")
   
   # Solution: Verify file_id consistency
   assert context.file_id in context.symbol_table._qname_to_id.values()
   ```

3. **Import Outside Function/Class Context**
   ```python
   # Problem: Import usage at module level (no consumer)
   # Module-level usage is not tracked by design
   import json
   data = json.loads('{}')  # This won't create an edge
   
   def process():
       json.loads('{}')  # This WILL create an edge
   ```

4. **Wildcard Imports (Not Supported)**
   ```python
   # Problem: Wildcard imports are not fully supported
   from pathlib import *
   from collections import *
   
   def process_data():
       path = Path("/data")        # NOT TRACKED - no dependency edge created
       count = Counter([1,2,3])    # NOT TRACKED - no dependency edge created
   
   # Solution: Use explicit imports instead
   from pathlib import Path
   from collections import Counter
   
   def process_data():
       path = Path("/data")        # ✅ TRACKED - creates dependency edge
       count = Counter([1,2,3])    # ✅ TRACKED - creates dependency edge
   ```

### Problem 2: Wildcard Import Limitations

**Symptoms:**
- Imports processed but no edges created for symbol usage
- Functions using imported symbols show no dependencies
- Analysis summary shows imports processed but zero edges

**Example Problem:**
```python
# problematic_wildcard.py
from pathlib import *
from collections import *
from itertools import *

def data_processing():
    # None of these create dependency edges:
    file_path = Path("data.txt")                    # pathlib.Path - MISSED
    counter = Counter([1, 2, 2, 3])                 # collections.Counter - MISSED
    combos = list(combinations(range(3), 2))        # itertools.combinations - MISSED
    
    return file_path, counter, combos

# Analysis results:
# - 3 imports processed ✓
# - 0 dependency edges created ✗
```

**Why This Happens:**
The dependency visitor currently **skips wildcard imports** due to implementation complexity:

```python
# In ImportProcessor.process_import_from():
for alias in node.names:
    if alias.name == '*':
        # Wildcard imports are skipped - symbols not registered
        continue
```

**Root Cause:**
- Wildcard symbols are not registered in the symbol table
- Symbol usage cannot be resolved to qualified names
- No dependency edges are created

**Solutions:**

1. **Use Explicit Imports (Recommended)**
   ```python
   # Replace wildcards with explicit imports
   from pathlib import Path, PurePath
   from collections import Counter, defaultdict, deque
   from itertools import combinations, permutations, chain
   
   def data_processing():
       file_path = Path("data.txt")                # ✅ Creates pathlib.Path edge
       counter = Counter([1, 2, 2, 3])             # ✅ Creates collections.Counter edge
       combos = list(combinations(range(3), 2))    # ✅ Creates itertools.combinations edge
   ```

2. **Use Module-Level Imports**
   ```python
   # Import entire modules instead
   import pathlib
   import collections
   import itertools
   
   def data_processing():
       file_path = pathlib.Path("data.txt")              # ✅ Creates pathlib.Path edge
       counter = collections.Counter([1, 2, 2, 3])       # ✅ Creates collections.Counter edge
       combos = list(itertools.combinations(range(3), 2)) # ✅ Creates itertools.combinations edge
   ```

3. **Mixed Approach**
   ```python
   # Keep wildcards for convenience, add explicit imports for tracking
   from pathlib import *
   from pathlib import Path, PurePath  # Explicit for analysis
   
   def data_processing():
       # Both work, but only explicit import creates edges
       file_path = Path("data.txt")  # ✅ Tracked via explicit import
   ```

**Diagnosis Script:**
```python
def diagnose_wildcard_imports(context, ast_tree):
    """Check for wildcard imports that might cause missing edges."""
    
    visitor = DependencyVisitor(context)
    visitor.visit(ast_tree)
    
    # Check for wildcard imports
    wildcard_imports = []
    for import_node in visitor.import_processor.get_processed_imports():
        if isinstance(import_node, ast.ImportFrom):
            for alias in import_node.names:
                if alias.name == '*':
                    wildcard_imports.append(import_node.module)
    
    if wildcard_imports:
        print(f"⚠️  Found {len(wildcard_imports)} wildcard imports:")
        for module in wildcard_imports:
            print(f"   - from {module} import *")
        print("   These imports won't create dependency edges for symbol usage")
        print("   Consider using explicit imports instead")
    
    # Check symbol table registration
    file_imports = context.symbol_table._file_id_to_imports.get(context.file_id, {})
    print(f"\n📊 Registered imports: {len(file_imports)}")
    for alias, qname in file_imports.items():
        print(f"   {alias} → {qname}")
    
    # Check edges created
    edges = [e for e in context.results if isinstance(e, UsesImportEdge)]
    print(f"\n🔗 Dependency edges created: {len(edges)}")
    
    return wildcard_imports, file_imports, edges
```

### Problem 3: Incorrect Target Resolution

**Symptoms:**
- Edges created with wrong `target_qname`
- Relative imports resolved incorrectly

**Diagnosis:**
```python
# Check relative import resolution
from .helpers import get_relative_import_base, get_file_qname_from_context

file_qname = get_file_qname_from_context(context)
print(f"Current file qname: {file_qname}")

# Test relative import resolution
for level in [1, 2, 3]:
    base = get_relative_import_base(context, level)
    print(f"Level {level} relative base: {base}")
```

**Common Causes & Solutions:**

1. **File QName Not Found**
   ```python
   # Problem: File not properly registered in symbol table
   file_qname = get_file_qname_from_context(context)
   if file_qname == "unknown_file":
       print("ERROR: File qname not found in symbol table")
   
   # Solution: Ensure file is properly registered
   context.symbol_table.add_symbol(expected_file_qname, context.file_id)
   ```

2. **Invalid Relative Import Level**
   ```python
   # Problem: More dots than package depth
   # from .... import something  # Too many dots
   
   # Solution: Validate import levels in get_relative_import_base()
   def get_relative_import_base(context, level):
       parts = file_qname.split('.')
       if level >= len(parts):
           logger.warning(f"Invalid relative import level {level}")
           return ""  # Return empty to avoid errors
   ```

### Problem 3: Performance Issues

**Symptoms:**
- Slow analysis on large files
- Memory usage growing significantly

**Diagnosis:**
```python
import time
import psutil

# Measure visitor performance
start_time = time.time()
start_memory = psutil.Process().memory_info().rss

visitor = DependencyVisitor(context)
visitor.visit(ast_tree)

end_time = time.time()
end_memory = psutil.Process().memory_info().rss

print(f"Analysis time: {end_time - start_time:.2f}s")
print(f"Memory delta: {(end_memory - start_memory) / 1024 / 1024:.2f}MB")
print(f"Edges created: {len(context.results)}")
```

**Optimization Strategies:**

1. **Limit Edge Creation**
   ```python
   # Add filtering to avoid excessive edges
   def create_usage_edge(context, consumer_id, target_qname, **kwargs):
       # Skip if too many edges already created
       if len(context.results) > MAX_EDGES_PER_FILE:
           logger.warning("Edge limit reached, skipping")
           return
       
       # Normal edge creation...
   ```

2. **Optimize Symbol Table Lookups**
   ```python
   # Cache frequently accessed data
   class OptimizedDependencyVisitor(DependencyVisitor):
       def __init__(self, context):
           super().__init__(context)
           self._file_qname_cache = get_file_qname_from_context(context)
           self._import_cache = {}
       
       def cached_resolve_import(self, name):
           if name not in self._import_cache:
               self._import_cache[name] = self.context.symbol_table.resolve_import_qname(
                   self.context.file_id, name
               )
           return self._import_cache[name]
   ```

## Performance Considerations

### Memory Management

```python
# Monitor memory usage during analysis
def analyze_with_memory_monitoring(context, ast_tree):
    visitor = DependencyVisitor(context)
    
    # Clear any existing results to start fresh
    context.results.clear()
    
    # Process in chunks for very large ASTs
    if len(ast_tree.body) > 1000:  # Arbitrary large threshold
        for chunk in chunk_ast_nodes(ast_tree.body, chunk_size=100):
            temp_ast = ast.Module(body=chunk, type_ignores=[])
            visitor.visit(temp_ast)
            
            # Optionally persist and clear results periodically
            if len(context.results) > 10000:
                persist_edges(context.results)
                context.results.clear()
    else:
        visitor.visit(ast_tree)
    
    return context.results
```

### Batch Processing

```python
# Process multiple files efficiently
def batch_analyze_dependencies(file_paths, symbol_table):
    all_edges = []
    
    for file_path in file_paths:
        try:
            # Parse file
            with open(file_path) as f:
                source = f.read()
            ast_tree = ast.parse(source)
            
            # Create context
            file_id = get_file_id(file_path)
            context = VisitorContext(file_id, ast_tree, symbol_table)
            
            # Run analysis
            visitor = DependencyVisitor(context)
            visitor.visit(ast_tree)
            
            # Collect results
            all_edges.extend(context.results)
            
            # Log progress
            print(f"Processed {file_path}: {len(context.results)} edges")
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            continue
    
    return all_edges
```

## Testing Strategies

### Unit Testing Components

```python
import pytest
from unittest.mock import Mock

def test_import_processor():
    # Setup
    symbol_table = Mock()
    context = Mock()
    context.symbol_table = symbol_table
    context.file_id = "test_file"
    
    processor = ImportProcessor(context)
    
    # Test regular import
    import_node = ast.parse("import json").body[0]
    processor.process_import(import_node)
    
    # Verify symbol table updated
    symbol_table.add_import.assert_called_with("test_file", "json", "json")

def test_usage_detector():
    # Setup mocks
    context = Mock()
    get_consumer_id = Mock(return_value="consumer_123")
    get_imports = Mock(return_value=[])
    
    detector = UsageDetector(context, get_consumer_id, get_imports)
    
    # Test name usage detection
    name_node = ast.parse("json").body[0].value
    context.symbol_table.resolve_import_qname.return_value = "json"
    
    detector.detect_name_usage(name_node)
    
    # Verify edge creation attempted
    assert len(context.results.append.call_args_list) == 1
```

### Integration Testing

```python
def test_full_dependency_analysis():
    # Prepare test code
    test_code = """
import json
from requests import get

def process_data():
    data = json.loads('{}')
    response = get('http://api.example.com')
    return data, response
"""
    
    # Setup
    ast_tree = ast.parse(test_code)
    symbol_table = SymbolTable()
    context = VisitorContext("test_file", ast_tree, symbol_table)
    
    # Run declaration visitor first
    decl_visitor = DeclarationVisitor(context)
    decl_visitor.visit(ast_tree)
    
    # Run dependency visitor
    dep_visitor = DependencyVisitor(context)
    dep_visitor.visit(ast_tree)
    
    # Verify results
    edges = [e for e in context.results if isinstance(e, UsesImportEdge)]
    assert len(edges) == 2  # json.loads and get usage
    
    # Verify edge details
    json_edge = next(e for e in edges if e.target_qname == "json.loads")
    assert json_edge.alias == "json"
    assert json_edge.target_symbol == "loads"
    
    get_edge = next(e for e in edges if e.target_qname == "requests.get") 
    assert get_edge.alias == "get"
    assert get_edge.target_symbol == "get"
```

This comprehensive guide covers all aspects of using and troubleshooting the dependency visitor system. 