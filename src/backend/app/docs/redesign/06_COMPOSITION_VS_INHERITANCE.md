### 06. Composition vs Inheritance Guidelines

Use composition when
- Adding capabilities without changing identity (attach properties, behaviors)
- Variants share base but differ in data (use `properties` models)
- Cross-cutting features (logging, caching) via decorators/adapters

Use inheritance when
- Sharing storage or protocol fields (`ArangoBase`, `BaseNode`, `BaseEdge`)
- Defining discriminated unions (leaf types extend base)

Avoid
- Deep hierarchies; prefer flat leaf types + composed properties
- Putting behavior in Pydantic models; keep behavior in domain wrappers

Patterns
- Value Objects for properties
- Aggregates for consistency boundaries
- Mixins for optional common interfaces (e.g., `HasPosition`) 