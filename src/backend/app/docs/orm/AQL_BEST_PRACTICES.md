### AQL Best Practices

Binding and safety
- Always use bind variables; never format user input into queries
- Centralize query snippets for reuse (avoid duplication)

Common patterns
- Filter + paginate:
  ```aql
  FOR doc IN nodes
    FILTER doc.node_type == @type
    SORT doc.qname ASC
    LIMIT @offset, @limit
    RETURN doc
  ```
- Upsert:
  ```aql
  UPSERT { _key: @key }
  INSERT @doc
  UPDATE @doc IN nodes
  RETURN NEW
  ```
- Traversal (descendants):
  ```aql
  FOR v, e, p IN 1..@maxDepth OUTBOUND @start @@edge
    RETURN v
  ```

Indexes
- Create hash indexes on equality-filtered fields; persistent for range/sort
- Use `ANALYZER()` and fulltext indexes only when needed

Performance
- Inspect plans with `EXPLAIN`; check index usage
- Limit result size; stream large results
- Prefer projection: `RETURN { _id: v._id, qname: v.qname }`

Transactions
- Group related writes with `db.transaction` when atomicity matters

Diagnostics
- Log query string + bind vars (sanitized) and latency for profiling 