### DTOs, Validation, and Versioning

DTOs
- Separate request/response models (Pydantic) per endpoint
- Avoid leaking internal domain structures

Validation
- Synchronous validation at transport boundary
- Business invariant validation in domain/services

Versioning
- Add `model_version` to nodes/edges for migrations
- Backward-compatible DTO changes; use `deprecated` fields with migration notes

## Step-by-step: Define DTOs with versioning

```python
from pydantic import BaseModel, Field

class ProjectResponse(BaseModel):
    key: str
    name: str
    path: str
    model_version: int = Field(default=2)
``` 