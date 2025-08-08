### Python Type Parsing & Inference Guide

#### Goals
- Extract explicit annotations and infer simple types to power call resolution and data modeling

#### Sources of types
- Function signatures: parameter annotations, return types (including deferred `from __future__ import annotations`)
- Class attributes: annotated `AnnAssign` and inferred from assignments in class body
- Local variables: simple inference from literals and constructor calls
- Aliases: `T = List[int]`, `UserId = str`

#### Parsing annotations
- Handle `Name`, `Attribute`, `Subscript` (generics)
- Normalize to strings; if Python ≥3.9 use `ast.unparse`, else implement visitor
- Support string annotations (PEP 563/649): evaluate safely or treat as strings

#### Inference heuristics
- Literals: int/float/str/bool/None/list/dict/tuple/set
- Constructor calls: if name resolves to local class qname → that class
- Variable references: use `VisitorContext.local_variable_types`
- Return statements: infer if explicit return type missing

#### Linking custom types
- If base type isn’t builtin and `SymbolIndex.isLocalModule(type)` → link to class ID
- Else for external types, link to package ID (top-level segment)

#### Edge cases
- Optional/Union/List/Dict nesting: extract base type for linking
- `typing` aliases and `from typing import List as L`: resolve imports first
- Dataclasses/Pydantic: detect common patterns to collect fields

#### Output
- Emit TypeFacts for:
  - functionReturnType
  - variableType (local)
  - classFieldType
  - aliasType
- Do not mutate DB in-pass; let GraphWriter persist updates in batch

#### Tests to add
- Annotated vs inferred parameters/returns
- Class attributes (annotated and assigned)
- Constructor-based inference
- String annotations and forward refs 