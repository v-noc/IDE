# app/db/context.py
from dataclasses import dataclass
from typing import Optional

from app.core.repository import Repositories
from app.core.model.nodes import ProjectNode
from app.db.async_terminus_client import AsyncClient


@dataclass(frozen=True)
class RequestDbContext:
    branch: str = "main"
    ref: Optional[str] = None  # commit id / ref
    compare_to: Optional[str] = None


@dataclass(frozen=True)
class DbTarget:
    db: str
    branch: str = "main"
    ref: Optional[str] = None
    team: str = "admin"
    repo: str = "local"


class ProjectUoW:
    def __init__(self, client: AsyncClient, project: Optional[ProjectNode], ctx: RequestDbContext):
        self.client = client
        self.project = project
        self.ctx = ctx

    def get_meta_repos(self) -> Repositories:

        return Repositories(self.client)

    def has_compare_to(self) -> bool:
        return self.ctx.compare_to is not None

    def get_project_repos(self, use_compare_to: bool = False) -> Repositories:
        if self.project is None:
            return Repositories(self.client)

        client_clone = self.client.clone()
        client_clone.db = self.project.db_name
        client_clone.branch = self.ctx.branch

        if use_compare_to and self.ctx.compare_to:
            client_clone.ref = self.ctx.compare_to
        else:
            client_clone.ref = self.ctx.ref
        return Repositories(client_clone)

    @property
    def readonly(self) -> bool:
        return self.ctx.ref is not None or self.ctx.compare_to is not None
