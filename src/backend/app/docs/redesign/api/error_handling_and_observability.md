### Error Handling & Observability

Error model
- Domain exceptions mapped to HTTP problem+json
- Include `type`, `title`, `status`, `detail`, `instance`

Logging
- Structured logs with operation IDs
- Include AQL timings and collection counts on writes

Tracing & Metrics
- Optional OpenTelemetry spans around service calls and AQL
- Counters for node/edge inserts, updates, skips

## Step-by-step: Map domain errors to HTTP problem+json

1) Define exceptions
```python
class DomainError(Exception):
    code = "domain-error"

class NotFound(DomainError):
    code = "not-found"
```

2) FastAPI exception handler
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(DomainError)
def handle_domain_error(request: Request, exc: DomainError):
    status = 404 if isinstance(exc, NotFound) else 400
    return JSONResponse(
        status_code=status,
        content={
            "type": f"urn:problem:{exc.code}",
            "title": exc.__class__.__name__,
            "status": status,
            "detail": str(exc),
            "instance": str(request.url),
        },
    )
```

3) Structured logging around writes
```python
logger.info("graph.write", extra={"node_count": len(nodes), "edge_count": len(edges), "ms": duration_ms})
``` 