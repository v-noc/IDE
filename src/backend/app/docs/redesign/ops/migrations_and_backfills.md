### Migrations & Backfills

Strategy
- Versioned migrations with `model_version`
- Non-blocking online migrations; dual-write when necessary

Backfills
- Queue-based backfill jobs (chunked)
- Idempotent writes; resume on failure

Indices
- Create indices before backfills
- Monitor query performance and adjust 