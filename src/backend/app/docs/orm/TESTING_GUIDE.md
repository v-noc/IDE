### Testing Guide

Strategy
- Unit-test ORM methods with a test DB; truncate between tests
- Unit-test domain services (`CodeGraphManager`) using the real ORM
- E2E test API with `TestClient`

Fixtures
- Test DB name via env; fixture to reset collections (`truncate()`)
- Builders for common nodes (project, folder, file)

Assertions
- Validate Pydantic model instances after reads
- For traversals, assert node counts and specific qnames

Examples
- `tests/unit/core/test_manager.py` creates two projects and verifies listing
- Add tests for edge uniqueness (e.g., `links_to`)

Performance
- Avoid large data volumes; mock AQL for heavy queries where not essential 