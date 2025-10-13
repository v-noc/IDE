from app.core.repository import Repositories
from app.core.model.logs import LogNode
from app.api.json_rpc.schemas import RegisterLogsParams


class LogService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, function_id: str, params: RegisterLogsParams):
        return self.repos.log_repo.create(log)
