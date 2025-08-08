### 04. ORM: Repositories and Unit of Work

Repositories
- NodeRepository
  - get(id), get_by_qname(qname)
  - add(node), update(node), remove(id)
  - find(filter, limit), paginate(filter, sort, offset, limit)
  - bulk_add(nodes), upsert(key, node)
- EdgeRepository(kind)
  - add(edge), bulk_add(edges)
  - remove_match(filter), find(filter, limit)
  - traverse(start_id, dir, minDepth, maxDepth)

Unit of Work
- Tracks new/dirty/deleted Nodes and Edges per request
- begin() → repositories bound to this UoW
- commit() → GraphWriter persists in batches (nodes then edges)
- rollback() → clear tracked state

GraphWriter
- bulkCreateNodes, bulkCreateEdges, bulkUpdateNodes
- Transaction boundary configurable (per UoW or per batch size)

Mapping
- Pydantic DTOs map 1:1 to storage
- Domain entities wrap DTOs; Repos convert both ways

Testing
- FakeRepos for unit tests; In-memory UoW to simulate commits 