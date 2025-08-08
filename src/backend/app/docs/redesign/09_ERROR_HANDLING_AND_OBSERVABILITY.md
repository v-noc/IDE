### 09. Error Handling and Observability

Errors
- Domain: ValidationError, NotFound, Conflict, InvariantViolation
- Infra: ConnectionError, QueryError, TransactionError
- Map to API status codes with structured payloads

Logging
- Structured logs with correlation IDs (request, uow)
- Log AQL and bind vars (sanitized) with latency and row counts

Metrics
- Counters: repo ops, errors by type; Histograms: AQL latency
- Traces: wrap UoW commit and key queries

Diagnostics
- Health endpoints: DB connectivity, index checks
- Background validators for referential integrity 