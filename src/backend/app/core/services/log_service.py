from typing import Optional, TYPE_CHECKING

from app.core.repository import Repositories
from app.core.model.logs import LogNode
from app.core.model.edges import LogToFunctionEdge, LogToLogEdge

if TYPE_CHECKING:
    from app.api.json_rpc.schemas import RegisterLogsParams


class LogService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(self, function_id: str, params: "RegisterLogsParams", parent_function_id: Optional[str] = None):
        log = LogNode(
            timestamp=params.timestamp,
            event_type=params.event_type.value if hasattr(
                params.event_type, "value") else params.event_type,
            message=params.message,
            duration_ms=params.duration_ms,
            chain_id=params.chain_id,
            payload=params.payload,
            result=params.result,
            error=params.error,
        )

        created = self.repos.log_repo.create(log)

        # Edge: log -> function
        self.repos.log_to_function_edges.create(
            LogToFunctionEdge(
                from_id=created.id,
                to_id=function_id,
                edge_type="log_to_function_edges",
            )
        )

        # Edge: log -> log (optional parent derived via parent_function + chain_id)
        if parent_function_id and params.chain_id:
            parent_log = self.repos.log_repo.find_enter_log(
                function_id=parent_function_id,
                chain_id=params.chain_id,
            )
            if parent_log:
                self.repos.log_to_log_edges.create(
                    LogToLogEdge(
                        from_id=created.id,
                        to_id=parent_log.id,  # type: ignore[attr-defined]
                    )
                )

        return created

    def get_parent_log(self, log_id: str):
        return self.repos.log_repo.find_parent_log(log_id)
