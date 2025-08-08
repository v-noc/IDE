### Connection and Config

Connection lifecycle
- Singleton client and memoized DB connection via `db/client.get_db()`
- Rebind when DB name changes (useful in tests)

Recommendations
- Timeouts and retries: configure `ArangoClient` with sensible timeouts
- Health checks: lightweight `db.version()` at startup or readiness probe
- Separate users/permissions per environment; principle of least privilege
- Connection pooling: rely on Arango client pool; keep connections per-process

Configuration
- Centralize in `config/settings.py` (already used) with env overrides
- Distinguish runtime vs test DBs; set `ARANGO_DB` per test session

Testing
- Fixture resets: `collections.*.truncate()` between tests or per suite
- Use ephemeral DB names like `v_noc_test_<pid>`; drop after tests
- Seed minimal indexes in setup; avoid migrating on every test

Observability
- Log connection errors with structured context
- Expose metrics: connection reuse count, AQL latency histograms 