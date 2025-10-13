from pydantic import BaseModel, Field


class RegisterLogsParams(BaseModel):
    """Params for register_logs JSON-RPC method."""

    project_id: str = Field(..., description="Project document key")
    element_id: str = Field(..., description="Code element document key")


class RegisterLogsResult(BaseModel):
    """Minimal result placeholder for register_logs."""

    ok: bool = Field(..., description="Operation acknowledgement")
