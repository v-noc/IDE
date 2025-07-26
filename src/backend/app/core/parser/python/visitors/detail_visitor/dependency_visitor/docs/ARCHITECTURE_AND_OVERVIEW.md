# Dependency Visitor Architecture & Overview

## Table of Contents
- [System Purpose](#system-purpose)
- [Architecture Overview](#architecture-overview)
- [Component Relationships](#component-relationships)
- [Data Flow](#data-flow)
- [Core Concepts](#core-concepts)
- [Integration Points](#integration-points)

## System Purpose

The **Dependency Visitor** is a sophisticated AST (Abstract Syntax Tree) analysis system designed to track and resolve Python import dependencies within a codebase. It identifies how modules, classes, and functions use imported symbols and creates structured dependency relationships for code analysis and visualization.

### Key Capabilities:
- **Import Resolution**: Processes all Python import statements (`import` and `from...import`)
- **Usage Tracking**: Detects where imported symbols are actually used in code
- **Context Awareness**: Maintains precise context about which function/class is using imports
- **Dependency Mapping**: Creates structured edges representing "uses" relationships
- **Local vs External**: Distinguishes between project-internal and external package dependencies

## Architecture Overview

The system follows a **modular, component-based architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                DependencyVisitor                        │
│                (Main Orchestrator)                      │
│  ┌─────────────────────────────────────────────────────┤
│  │ Coordinates all components and manages AST visiting  │
│  └─────────────────────────────────────────────────────┤
└─────────────────┬───────────────────┬───────────────────┘
                  │                   │
    ┌─────────────▼─────────────┐    ┌▼──────────────────────┐
    │    ImportProcessor        │    │  DependencyContext    │
    │                          │    │      Manager          │
    │ • Processes import stmts  │    │                      │
    │ • Handles aliases         │    │ • Tracks current     │
    │ • Registers in SymTable   │    │   function/class     │
    │ • Relative imports        │    │ • Manages scope      │
    └─────────────┬─────────────┘    │ • Context switching  │
                  │                  └──────────┬───────────┘
                  │                             │
            ┌─────▼─────────────────────────────▼─────┐
            │           UsageDetector                 │
            │                                        │
            │ • Detects symbol usage (ast.Name)      │
            │ • Handles attribute chains             │
            │ • Creates UsesImportEdge objects       │
            │ • Position tracking                    │
            └────────────────┬───────────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Helpers      │
                    │                 │
                    │ • Utility funcs │
                    │ • Edge creation │
                    │ • Qname resolve │
                    │ • Chain parsing │
                    └─────────────────┘
```

## Component Relationships

### 1. **DependencyVisitor** (Main Orchestrator)
- **Role**: Central coordinator that implements `ast.NodeVisitor`
- **Responsibilities**: 
  - Routes AST nodes to appropriate specialists
  - Manages component lifecycle
  - Provides unified interface
  - Collects analysis results

### 2. **ImportProcessor**
- **Role**: Import statement specialist
- **Dependencies**: Uses `VisitorContext` and `helpers.py`
- **Outputs**: Updates `SymbolTable` with import mappings

### 3. **DependencyContextManager**
- **Role**: Context tracking specialist
- **Dependencies**: Uses `VisitorContext` and `helpers.py`
- **Outputs**: Provides current consumer ID for edge creation

### 4. **UsageDetector**
- **Role**: Symbol usage specialist
- **Dependencies**: Uses output from ImportProcessor and ContextManager
- **Outputs**: Creates `UsesImportEdge` objects

### 5. **Helpers Module**
- **Role**: Shared utilities
- **Users**: All other components
- **Functions**: Common operations like qname resolution, edge creation

## Data Flow

### Phase 1: Import Discovery
```
AST Import Nodes → ImportProcessor → SymbolTable Registration
                                  ↓
                              Import Registry
                           (alias → qname mapping)
```

### Phase 2: Context Establishment
```
AST FunctionDef/ClassDef → DependencyContextManager → Current Consumer ID
                                                   ↓
                                               Active Context
                                            (for edge creation)
```

### Phase 3: Usage Detection & Edge Creation
```
AST Name/Attribute Nodes → UsageDetector → Lookup in SymbolTable
                                         ↓
                              Create UsesImportEdge → Context.results
```

## Core Concepts

### Symbol Resolution Chain
1. **Import Registration**: `alias → qname` mapping stored in SymbolTable
2. **Usage Detection**: AST nodes checked against registered imports
3. **Context Application**: Current function/class provides the "from" node
4. **Edge Creation**: Structured dependency relationship created

### Context Management
- **Consumer**: The function or class that uses an import
- **Context Stack**: Nested scopes handled through push/pop mechanism
- **Scope Isolation**: Each function/class gets its own analysis context

### Import Types Handled
- **Simple imports**: `import os` → `os` alias maps to `os` qname
- **Aliased imports**: `import numpy as np` → `np` alias maps to `numpy` qname
- **From imports**: `from os import path` → `path` alias maps to `os.path` qname
- **Aliased from imports**: `from os import path as p` → `p` alias maps to `os.path` qname
- **Relative imports**: `from .utils import helper` → resolved to absolute qname

### Edge Types Created
- **UsesImportEdge**: Represents dependency relationship
  - `_from`: Database ID of consuming function/class
  - `_to`: Database ID of target symbol (resolved later)
  - `target_symbol`: Specific symbol being used
  - `alias`: Alias used in the code
  - `import_position`: Where the import statement appears
  - `usage_positions`: All locations where the symbol is used

## Integration Points

### With Symbol Table System
- **Input**: Receives SymbolTable instance through VisitorContext
- **Output**: Registers discovered imports for later resolution
- **Interaction**: Bidirectional - writes imports, reads for resolution

### With AST Analysis Pipeline
- **Position**: Runs after DeclarationVisitor but before other detail visitors
- **Input**: Clean AST tree and populated SymbolTable
- **Output**: UsesImportEdge objects in context.results

### With Database Layer
- **Edge Storage**: Created edges are persisted as graph relationships
- **Node Resolution**: Target qnames resolved to actual database IDs
- **Relationship Queries**: Enables dependency graph queries

### With Project Scanner
- **Integration**: Scanner orchestrates visitor execution
- **Batch Processing**: Handles multiple files efficiently
- **Result Aggregation**: Collects edges from all files

This architecture ensures **scalability**, **maintainability**, and **precise dependency tracking** across large Python codebases.

## Current Limitations

### Wildcard Import Support
- **Status**: Limited support for `from module import *` syntax
- **Behavior**: Wildcard imports are recorded but individual symbols are not registered
- **Impact**: Usage of wildcard-imported symbols won't create dependency edges
- **Workaround**: Use explicit imports (`from module import symbol1, symbol2`) for full tracking

### Module-Level Usage
- **Status**: Dependencies only tracked within function/class context
- **Impact**: Import usage at module level (outside functions/classes) is not tracked
- **Design**: Intentional to focus on consumable code units

### Complex Expressions
- **Status**: Only simple attribute chains are resolved
- **Example**: `requests.get().json()` - only `requests.get` is tracked
- **Impact**: Method calls on returned objects are not considered import usage 