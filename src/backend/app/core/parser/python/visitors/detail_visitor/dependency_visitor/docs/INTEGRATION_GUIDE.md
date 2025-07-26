# Dependency Visitor Integration Guide

## Table of Contents
- [System Integration Overview](#system-integration-overview)
- [Pipeline Integration](#pipeline-integration)
- [Symbol Table Integration](#symbol-table-integration)
- [Database Integration](#database-integration)
- [Result Processing](#result-processing)
- [Error Handling](#error-handling)

## System Integration Overview

The Dependency Visitor is a **critical component** in the v-noc code analysis pipeline, positioned strategically between symbol declaration processing and database persistence. It operates as part of a multi-stage AST analysis system.

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Project Scanner                          │
│                   (Orchestrator)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │      File Parser          │
         │                          │
         │ • Parses Python files     │
         │ • Creates AST trees       │
         │ • Initializes SymbolTable │
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │   Declaration Visitor     │
         │                          │
         │ • Discovers functions     │
         │ • Discovers classes       │
         │ • Populates SymbolTable   │
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │   Dependency Visitor      │  ← THIS MODULE
         │                          │
         │ • Processes imports       │
         │ • Tracks usage            │
         │ • Creates dependency edges│
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │    Other Detail Visitors  │
         │                          │
         │ • Type inference          │
         │ • Control flow            │
         │ • etc.                   │
         └─────────────┬─────────────┘
                       │
         ┌─────────────▼─────────────┐
         │    Database Persistence   │
         │                          │
         │ • Stores nodes            │
         │ • Stores edges            │
         │ • Resolves references     │
         └───────────────────────────┘
```

## Pipeline Integration

### Execution Order

The dependency visitor **must run after** the Declaration Visitor to ensure all local symbols are registered in the SymbolTable before dependency resolution begins.

```python
# Typical execution flow in PythonFileParser
class PythonFileParser:
    def parse_file(self, file_path: str) -> List[BaseEdge]:
        # 1. Parse AST
        ast_tree = ast.parse(source_code)
        
        # 2. Initialize context
        context = VisitorContext(file_id, ast_tree, symbol_table)
        
        # 3. REQUIRED: Run declaration visitor first
        declaration_visitor = DeclarationVisitor(context)
        declaration_visitor.visit(ast_tree)
        
        # 4. Run dependency visitor (this module)
        dependency_visitor = DependencyVisitor(context)
        dependency_visitor.visit(ast_tree)
        
        # 5. Run other detail visitors
        # ... other visitors
        
        return context.results
```

### Context Sharing

All visitors share a **common VisitorContext** object that maintains:

```python
class VisitorContext:
    file_id: str              # Database ID of current file
    ast: ast.Module           # Shared AST tree
    symbol_table: SymbolTable # Shared symbol resolution engine
    results: List[BaseEdge]   # Accumulated edges from all visitors
```

**Critical Requirements:**
- SymbolTable must be populated with local symbols **before** dependency analysis
- All visitors append to the same `results` list
- File ID must be consistent across all visitors

## Symbol Table Integration

### SymbolTable Interface

The dependency visitor interacts with the SymbolTable through specific methods:

#### Reading Operations
```python
# Resolve imported names to fully qualified names
resolved_qname = symbol_table.resolve_import_qname(file_id, name)

# Check if qname refers to local vs external module
is_local = symbol_table.is_local_module(qname)

# Access internal mappings (for qname construction)
node_id = symbol_table._qname_to_id.get(qname)
```

#### Writing Operations
```python
# Register discovered imports (done by ImportProcessor)
symbol_table.add_import(file_id, alias, qname)
```

### Symbol Table Population Flow

```
Declaration Visitor:
├── Functions   → symbol_table.add_symbol("myfile.my_function", func_id)
├── Classes     → symbol_table.add_symbol("myfile.MyClass", class_id)
└── Variables   → symbol_table.add_symbol("myfile.my_var", var_id)

Dependency Visitor:
├── Imports     → symbol_table.add_import(file_id, "np", "numpy")
├── Usage       → symbol_table.resolve_import_qname(file_id, "np")
└── Resolution  → Creates edges using resolved qnames
```

### Integration Example

```python
# In Declaration Visitor (runs first)
def visit_FunctionDef(self, node):
    qname = f"{self.file_qname}.{node.name}"
    func_id = create_function_node(qname)
    self.symbol_table.add_symbol(qname, func_id)

# In Dependency Visitor (runs after)
def visit_Import(self, node):
    for alias in node.names:
        self.symbol_table.add_import(
            self.context.file_id, 
            alias.asname or alias.name,
            alias.name
        )

def visit_Name(self, node):
    # This resolution depends on Declaration Visitor having run
    resolved = self.symbol_table.resolve_import_qname(
        self.context.file_id, 
        node.id
    )
```

## Database Integration

### Edge Creation and Storage

The dependency visitor creates `UsesImportEdge` objects that are later persisted to the database:

```python
# Created by dependency visitor
edge = UsesImportEdge(
    _from="function_db_id_123",           # Known from SymbolTable
    _to="",                               # Will be resolved by scanner
    target_symbol="Request",
    alias="Request", 
    import_position=NodePosition(...),
    usage_positions=[NodePosition(...)]
)

# Custom attribute for scanner resolution
edge.target_qname = "fastapi.Request"    # Full qualified name

# Added to shared results
context.results.append(edge)
```

### Two-Phase Resolution

**Phase 1: Local Resolution (Dependency Visitor)**
- Resolves imports to fully qualified names
- Creates edges with known `_from` IDs (local functions/classes)
- Leaves `_to` field empty for external resolution

**Phase 2: External Resolution (Project Scanner)**
- Processes all collected edges
- Resolves `target_qname` to actual database IDs
- Creates external package nodes if needed
- Updates `_to` field with resolved IDs

### Database Schema Integration

```sql
-- Nodes table
Nodes:
  _id: "func_123"
  node_type: "function"
  qname: "myproject.utils.helper"

-- Edges table  
Edges:
  _from: "func_123"           -- Consumer function
  _to: "package_456"          -- Target package/symbol
  edge_type: "uses_import"
  target_symbol: "Request"
  alias: "Request"
```

## Result Processing

### Result Collection Flow

```python
# Each file produces a list of edges
file1_results = [UsesImportEdge(...), UsesImportEdge(...)]
file2_results = [UsesImportEdge(...)]

# Scanner aggregates all results
all_edges = []
for file_path in project_files:
    file_edges = parser.parse_file(file_path)
    all_edges.extend(file_edges)

# Batch processing for efficiency
scanner.process_edges_batch(all_edges)
```

### Edge Processing Pipeline

```
Individual File Analysis:
├── Raw AST → DependencyVisitor → UsesImportEdge objects
└── Store in context.results

Project-Level Aggregation:
├── Collect edges from all files
├── Group by target_qname for efficiency
└── Resolve external dependencies

Database Persistence:
├── Create package nodes for external dependencies
├── Update edge _to fields with resolved IDs
└── Batch insert edges
```

## Error Handling

### Integration Error Scenarios

#### Missing Declaration Data
```python
# Problem: Declaration visitor didn't run or failed
function_id = symbol_table._qname_to_id.get(function_qname)
if not function_id:
    # Cannot create dependency edge - no consumer context
    logger.warning(f"Function {function_qname} not found in symbol table")
    return
```

#### Invalid Import Resolution
```python
# Problem: Malformed import or resolution failure
resolved_qname = symbol_table.resolve_import_qname(file_id, name)
if not resolved_qname:
    # Import not found - could be built-in or undefined
    return  # Skip creating edge
```

#### Context Corruption
```python
# Problem: Multiple visitors modifying context incorrectly
if not isinstance(context.symbol_table, SymbolTable):
    raise IntegrationError("Invalid symbol table in context")

if context.file_id not in context.symbol_table._file_id_to_imports:
    logger.warning(f"No imports registered for file {context.file_id}")
```

### Error Recovery Strategies

#### Graceful Degradation
```python
def create_usage_edge(context, consumer_id, target_qname, **kwargs):
    try:
        edge = UsesImportEdge(
            _from=consumer_id,
            _to="",
            target_qname=target_qname,
            **kwargs
        )
        context.results.append(edge)
    except Exception as e:
        logger.error(f"Failed to create usage edge: {e}")
        # Continue processing other edges
```

#### Validation Checkpoints
```python
def validate_integration_state(context):
    """Validates that integration requirements are met."""
    assert context.symbol_table is not None
    assert context.file_id in context.symbol_table._qname_to_id.values()
    assert isinstance(context.results, list)
```

### Integration Testing

```python
def test_dependency_visitor_integration():
    # Setup: Ensure proper execution order
    context = create_test_context()
    
    # 1. Declaration visitor must run first
    decl_visitor = DeclarationVisitor(context)
    decl_visitor.visit(test_ast)
    
    # 2. Verify symbol table populated
    assert len(context.symbol_table._qname_to_id) > 0
    
    # 3. Run dependency visitor
    dep_visitor = DependencyVisitor(context)
    dep_visitor.visit(test_ast)
    
    # 4. Verify edges created
    edges = [e for e in context.results if isinstance(e, UsesImportEdge)]
    assert len(edges) > 0
    
    # 5. Verify edge integrity
    for edge in edges:
        assert edge._from  # Must have consumer ID
        assert edge.target_qname  # Must have target for resolution
```

This integration guide ensures proper coordination between the dependency visitor and all other system components. 