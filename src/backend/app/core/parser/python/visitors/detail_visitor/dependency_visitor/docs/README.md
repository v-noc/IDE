# Dependency Visitor Documentation Suite

## Overview

This directory contains comprehensive documentation for the **Dependency Visitor** system, a sophisticated Python AST analysis component that tracks import dependencies and creates structured dependency relationships for code analysis and visualization.

## Documentation Structure

### 📖 [Architecture & Overview](./ARCHITECTURE_AND_OVERVIEW.md)
**Start here for system understanding**
- System purpose and capabilities
- Component-based architecture design
- Data flow and core concepts
- Integration points with broader system
- Visual architecture diagrams

### 🔧 [API Reference](./API_REFERENCE.md)
**Complete technical reference**
- Detailed API documentation for all classes
- Method signatures and parameters
- Usage examples for each component
- Data model specifications
- Return types and error conditions

### 🔗 [Integration Guide](./INTEGRATION_GUIDE.md)
**System integration details**
- Pipeline integration requirements
- Symbol table coordination
- Database integration patterns
- Error handling strategies
- Integration testing approaches

### 💡 [Usage Examples & Troubleshooting](./USAGE_EXAMPLES.md)
**Practical usage guide**
- Basic and advanced usage scenarios
- Common dependency patterns
- Step-by-step troubleshooting guide
- Performance optimization strategies
- Testing methodologies

### 📚 [Glossary & Terms](./GLOSSARY_AND_TERMS.md)
**Reference for all terminology**
- Core concepts and definitions
- Variable naming conventions
- Data structure specifications
- Algorithm terminology
- System component glossary

## Quick Start

### 1. Understanding the System
Begin with the [Architecture & Overview](./ARCHITECTURE_AND_OVERVIEW.md) to understand:
- What the dependency visitor does
- How components work together
- Where it fits in the analysis pipeline

### 2. Implementation Details
Consult the [API Reference](./API_REFERENCE.md) for:
- Class constructors and methods
- Parameter specifications
- Expected return values

### 3. Integration Requirements
Review the [Integration Guide](./INTEGRATION_GUIDE.md) to understand:
- Execution order requirements
- Symbol table dependencies
- Context management needs

### 4. Practical Usage
Use [Usage Examples](./USAGE_EXAMPLES.md) for:
- Real-world implementation scenarios
- Debugging common issues
- Performance optimization

### 5. Term Reference
Reference the [Glossary](./GLOSSARY_AND_TERMS.md) for:
- Unfamiliar terminology
- Variable naming patterns
- System component roles

## System Summary

The **Dependency Visitor** is a modular AST analysis system that consists of four main components:

```
DependencyVisitor (Orchestrator)
├── ImportProcessor      # Processes import statements
├── ContextManager       # Tracks analysis context  
├── UsageDetector       # Detects symbol usage
└── Helpers             # Utility functions
```

### Key Features:
- **Import Resolution**: Handles all Python import forms including relative imports
- **Usage Tracking**: Detects where imported symbols are actually used
- **Context Awareness**: Maintains precise function/class context for edges
- **Dependency Mapping**: Creates structured `UsesImportEdge` relationships
- **Local vs External**: Distinguishes project-internal from external dependencies

### Input/Output:
- **Input**: AST tree, populated SymbolTable, VisitorContext
- **Output**: List of `UsesImportEdge` objects representing dependencies
- **Integration**: Part of multi-stage AST analysis pipeline

## Common Use Cases

### 1. Code Analysis
```python
# Analyze import dependencies in a Python file
visitor = DependencyVisitor(context)
visitor.visit(ast_tree)
edges = [e for e in context.results if isinstance(e, UsesImportEdge)]
```

### 2. Dependency Graph Construction
```python
# Build dependency relationships for visualization
for edge in dependency_edges:
    graph.add_edge(edge._from, edge.target_qname, 
                  symbol=edge.target_symbol, alias=edge.alias)
```

### 3. Import Usage Analysis
```python
# Get summary of import processing
summary = visitor.get_analysis_summary()
print(f"Processed {summary['total_imports_processed']} import statements")
print(f"Created {summary['total_edges_created']} dependency relationships")
```

## Prerequisites

Before using the dependency visitor, ensure:

1. **Declaration Visitor Executed**: Symbol table populated with local symbols
2. **VisitorContext Initialized**: Proper context with file ID, AST, and symbol table
3. **Database Integration**: System configured for edge persistence
4. **Error Handling**: Proper exception handling for analysis failures

## Integration Requirements

### Critical Dependencies:
- **SymbolTable**: Must be pre-populated with local symbols
- **VisitorContext**: Shared state management across all visitors  
- **AST Tree**: Parsed and validated Python AST
- **Database Layer**: For edge persistence and node resolution

### Execution Order:
1. **File Parsing**: Create AST and initialize context
2. **Declaration Analysis**: Populate symbol table with local symbols
3. **Dependency Analysis**: Run dependency visitor ← **This system**
4. **Additional Analysis**: Run other detail visitors
5. **Database Persistence**: Store results in graph database

## Performance Characteristics

- **Memory Usage**: ~1-5MB per 1000 lines of analyzed code
- **Processing Speed**: ~500-2000 lines/second (varies by import complexity)
- **Scalability**: Linear with number of import statements and usage sites
- **Optimization**: Caching available for repeated symbol lookups

## Troubleshooting Quick Reference

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| No edges created | Declaration visitor didn't run first | Ensure proper execution order |
| Wrong target resolution | File qname not in symbol table | Verify file registration |
| Missing usage detection | Import outside function/class | Check consumer context |
| Performance issues | Large files or many imports | Enable caching, limit edge creation |

## Contributing to Documentation

When updating this documentation:

1. **Maintain Consistency**: Follow established terminology and patterns
2. **Include Examples**: Provide concrete code examples for all concepts
3. **Update Cross-References**: Ensure links between documents remain valid
4. **Test Examples**: Verify all code examples actually work
5. **Version Updates**: Update version numbers and compatibility information

## Version Information

- **Current Version**: Compatible with Python 3.8+
- **AST Compatibility**: Python AST module (standard library)
- **Database Requirements**: ArangoDB for graph storage
- **Framework Integration**: Part of v-noc code analysis system

This documentation suite provides complete coverage of the dependency visitor system, from high-level architecture to implementation details and troubleshooting guides. 