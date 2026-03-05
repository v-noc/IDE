from typing import TYPE_CHECKING, List

from app.core.model.logs import LogNode
from app.core.model.schemas import FunctionSchema, LogSchema
from app.db.context import ProjectUoW

if TYPE_CHECKING:
    from app.api.json_rpc.schemas import RegisterLogsParams

from app.core.builder.log_tree_builder import LogTreeBuilder
from app.core.socket.manager import get_socket_manager


class LogService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.socket_manager = get_socket_manager()

    async def get_function_log(self, function_id: str):
        flat_logs = await self.uow.get_project_repos().log_repo.get_function_log(function_id)

        return LogTreeBuilder(flat_logs).build()

    async def get_parent_log(self, log_id: str):
        return await self.uow.get_project_repos().log_repo.get_parent_log(log_id)

    async def create_batch(self, batch_params: List["RegisterLogsParams"]):

        log_docs = []
        log_edges = []

        for p in batch_params:

            # Assuming 'p' is a dict or RegisterLogsParams object
            # Adapt this extraction based on your exact input format

            function_id = p.function_id
            if not function_id.startswith(FunctionSchema.__name__):
                function_id = f"{FunctionSchema.__name__}/{function_id}"
            log_docs.append(LogNode(
                id=f"{LogSchema.__name__}/{p.id}",
                timestamp=p.timestamp,
                event_type=p.event_type,
                message=p.message,
                level_name=p.level_name,
                origin_function=function_id,
                duration_ms=p.duration_ms,
                chain_id=p.chain_id,
                children_logs=set(),
                payload=p.payload,
                result=p.result,
                error=p.error,
            ))

            if p.parent_log_id:
                log_edges.append((
                    f"{LogSchema.__name__}/{p.id}",
                    f"{LogSchema.__name__}/{p.parent_log_id}",
                    "log"
                ))

        result = await self.uow.get_project_repos().log_repo.flush_batch_logs(log_docs, log_edges)
        if not result:
            return False

        # We get back objects with valid .id properties

        # Emit logs:new socket events for unique function_ids
        try:
            unique_function_ids = set(
                p.function_id for p in batch_params if p.function_id)
            for function_id in unique_function_ids:
                await self.socket_manager.emit_to_project(
                    self.uow.project.id,
                    "logs:new",
                    {"node_id": function_id}
                )
        except Exception as e:
            # Non-fatal: failure to emit socket event should not block log creation
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to emit logs:new socket events: {e}")

        return True
