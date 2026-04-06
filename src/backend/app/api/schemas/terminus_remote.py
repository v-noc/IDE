from urllib.parse import quote

from pydantic import BaseModel, Field, model_validator


class RemoteAuth(BaseModel):
    """Credentials sent to Terminus for remote operations (clone, push, pull)."""

    type: str = Field(
        default="http_basic",
        description="http_basic | token | bearer",
    )
    username: str | None = Field(
        default=None,
        description="Required for http_basic",
    )
    key: str = Field(..., description="Password, API key, or token value")

    @model_validator(mode="after")
    def _validate_http_basic(self):
        if self.type == "http_basic" and not self.username:
            raise ValueError("username is required when type is http_basic")
        return self


class RemoteConfig(BaseModel):
    """Remote Terminus target for project creation."""

    remote_url: str = Field(
        ...,
        description=(
            "For create_remote: normal server base URL (e.g. https://host:6363). "
            "For clone: full clone URL including team and database id."
        ),
    )
    auth: RemoteAuth
    team: str | None = Field(
        default=None,
        description=(
            "Remote team; defaults to TERMINUS_TEAM from settings when omitted."
        ),
    )


def remote_auth_to_header_dict(auth: RemoteAuth) -> dict:
    return auth.model_dump()


def clone_source_for_remote_database(
    server_base_url: str,
    team: str,
    db_name: str,
) -> str:
    """Build clone_source URL for a DB on the remote (Terminus _cloneable_url shape)."""
    base = server_base_url.rstrip("/")
    return f"{base}/{quote(team, safe='')}/{quote(db_name, safe='')}"
