### Migrations and Indexing

Versioning
- Maintain `schema_version` at app level and `model_version` per document
- Store migration history; upgrade on startup or via CLI

Migrations
- Backfill computed fields (e.g., normalized `qname`)
- Add new indexes; create safely (idempotent) and online if possible
- Data transforms: read in batches, `UPSERT` updated docs

Index strategy
- Nodes:
  - hash: `node_type`, `qname`
  - persistent: `properties.position.line_no` (if filtered/sorted)
- Edges:
  - hash: `_from`, `_to`, `edge_type`
  - unique: as required via `model_config.unique_on`

Validation
- Write a validator job to ensure edge endpoints exist

Tooling
- Provide `manage.py`/CLI commands: `migrate`, `create-indexes`, `verify` 