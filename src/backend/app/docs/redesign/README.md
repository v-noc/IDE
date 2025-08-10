### Redesign Proposal: Index

This documentation is organized into focused sections for depth and clarity.

- Architecture
  - [Overview](architecture/overview.md)
  - [Layered Design & Cross-Cutting Concerns](architecture/layers_and_concerns.md)
  - [Concurrency, Scaling, and Bulk Operations](architecture/concurrency_and_scaling.md)
- Domain
  - [Modeling & Aggregates](domain/modeling_and_aggregates.md)
  - [Identifiers, QNames, and Invariants](domain/identifiers_and_invariants.md)
  - [Relationships & Edge Semantics](domain/relationships_and_edges.md)
- Data & Persistence
  - [Graph Schema & Indices](data/schema_and_indices.md)
  - [Repositories & Unit of Work](data/repositories_and_uow.md)
  - [GraphWriter & Transactions](data/graph_writer_and_transactions.md)
- API & Services
  - [Service Layer & CQRS](api/service_layer_and_cqrs.md)
  - [DTOs, Validation, and Versioning](api/dtos_validation_versioning.md)
  - [Error Handling & Observability](api/error_handling_and_observability.md)
- Operations
  - [Migrations & Backfills](ops/migrations_and_backfills.md)
  - [Testing Strategy](ops/testing_strategy.md)
- Migration Plan
  - [Incremental Migration Plan](migration/plan.md)
- Examples & Recipes
  - [End-to-End Examples](examples/e2e_examples.md)
  - [Common Recipes](examples/recipes.md)

Legacy single-file docs remain for reference:
- [01. Architecture Overview](01_ARCHITECTURE_OVERVIEW.md)
- [02. Domain Modeling](02_DOMAIN_MODELING.md)
- [03. Graph Schema and Indices](03_GRAPH_SCHEMA_AND_INDICES.md)
- [04. ORM: Repositories and Unit of Work](04_ORM_REDESIGN_REPOSITORIES_AND_UOW.md)
- [05. Module Boundaries and Package Layout](05_MODULE_BOUNDARIES_AND_PACKAGE_LAYOUT.md)
- [06. Composition vs Inheritance Guidelines](06_COMPOSITION_VS_INHERITANCE.md)
- [07. Patterns and Extensibility](07_PATTERNS_AND_EXTENSIBILITY.md)
- [08. API Service Layer and CQRS](08_API_SERVICE_LAYER_AND_CQRS.md)
- [09. Error Handling and Observability](09_ERROR_HANDLING_AND_OBSERVABILITY.md)
- [10. Migration Plan](10_MIGRATION_PLAN.md)
- [11. Examples and Recipes](11_EXAMPLES_AND_RECIPES.md)

---

Tip: Each page now includes a "Step-by-step" section with runnable-style code examples and checklists. 