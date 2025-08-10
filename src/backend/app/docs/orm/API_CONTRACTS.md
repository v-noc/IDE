### ORM API Contracts

Node ORM
- get(key): T | None
- create(doc: T): T
- update(doc: T): T
- delete(key: str): bool
- find(filters: dict, limit?: int): list[T]
- find_one(filters: dict): T | None
- aql(query: str, bind_vars?: dict): list[T]
- find_like(field: str, pattern: str, limit?: int): list[T]
- truncate(): void
- bulk_create(docs: list[T]): list[T]
- upsert(key: str, doc: T): T
- paginate(filters: dict, sort: list[str], offset: int, limit: int): Page[T]

Edge ORM
- get(key): T | None
- create(edge: T): T
- delete(filters: dict): int
- update(edge: T): T
- find(filters: dict, limit?: int): list[T]
- find_one(filters: dict): T | None
- truncate(): void
- traverse(start_id: str, edge: str, dir: 'outbound'|'inbound'|'any', minDepth=1, maxDepth=3): list
- bulk_create(edges: list[T]): list[T]

Types
- Page<T> = { items: list[T], total: int, hasMore: bool, nextOffset: int }

Errors
- Wrap Arango errors into domain exceptions (e.g., NotFound, Conflict, Validation) 