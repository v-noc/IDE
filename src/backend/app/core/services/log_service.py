from typing import Optional, TYPE_CHECKING, List

from app.core.repository import Repositories
from app.core.model.logs import LogNode
from app.core.model.edges import LogToFunctionEdge, LogToLogEdge
from app.core.schemas.log_tree import LogTreeNode

if TYPE_CHECKING:
    from app.api.json_rpc.schemas import RegisterLogsParams

from app.core.builder.log_tree_builder import LogTreeBuilder
from app.core.socket.manager import get_socket_manager


class LogService:
    def __init__(self, repos: Repositories):
        self.repos = repos
        self.socket_manager = get_socket_manager()

    async def create(
        self,
        function_id: str,
        params: "RegisterLogsParams",
        parent_function_id: Optional[str] = None,
    ):
        log = LogNode(
            timestamp=params.timestamp,
            event_type=params.event_type.value
            if hasattr(params.event_type, "value")
            else params.event_type,
            message=params.message,
            level_name=getattr(params, "level_name", None),
            duration_ms=params.duration_ms,
            chain_id=params.chain_id,
            payload=params.payload,
            result=params.result,
            error=params.error,
        )

        created = await self.repos.log_repo.create(log)

        # Edge: log -> function
        await self.repos.log_to_function_edges.create(
            LogToFunctionEdge(
                from_id=created.id,
                to_id=function_id,
            )
        )

        await self._link_to_parent_log(
            created, function_id, parent_function_id, params.chain_id
        )

        # Emit logs:new socket event
        try:
            # Get project_id from function_id
            project_id = await self._get_project_id_from_node(function_id)
            if project_id:
                await self.socket_manager.emit_to_project(
                    project_id,
                    "logs:new",
                    {"node_id": function_id}
                )
        except Exception as e:
            # Non-fatal: failure to emit socket event should not block log creation
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to emit logs:new socket event: {e}")

        return created

    async def _link_to_parent_log(
        self,
        created_log: LogNode,
        function_id: str,
        parent_function_id: Optional[str],
        chain_id: Optional[str],
    ):
        if not chain_id:
            return

        parent_log = None

        # If not an enter event, first try to find parent within
        # the same function
        if created_log.event_type != "enter":
            parent_log = await self.repos.log_repo.find_enter_log(
                function_id=function_id,
                chain_id=chain_id,
            )

        # If it's an enter event, or no parent was found in the same function,
        # check the parent function
        if not parent_log and parent_function_id:
            parent_log = await self.repos.log_repo.find_enter_log(
                function_id=parent_function_id,
                chain_id=chain_id,
            )

        if parent_log:
            await self.repos.log_to_log_edges.create(
                LogToLogEdge(
                    from_id=created_log.id,
                    to_id=parent_log.id,
                )
            )

    async def get_parent_log(self, log_id: str):
        return await self.repos.log_repo.find_parent_log(log_id)

    async def get_function_log(self, function_id: str):
        flat_logs = await self.repos.log_repo.find_function_log(function_id)

        return LogTreeBuilder(flat_logs).build()

    async def get_log_containment_tree(self, log_id: str):
        """Gets all descendant logs for a given log ID and builds a tree."""
        flat_descendants = await self.repos.log_repo.get_containment_tree(log_id)

        root_log = await self.repos.log_repo.get_by_id(log_id)
        if not root_log:
            return []

        flat_list = [{"vertex": root_log.model_dump(
            by_alias=True), "parent_id": None}]
        flat_list.extend(flat_descendants)

        return LogTreeBuilder(flat_list).build()

    async def get_call_log(self, call_id: str) -> List[LogTreeNode]:
        # 1. Find the function that was called
        callees = await self.repos.call_repo.get_target(call_id)
        if not callees:
            return []
        called_function_id = callees.id

        # 2. Find the full function call chain
        function_docs_result = await self.repos.call_repo.find_upward_call_chain(
            call_id
        )
        if not function_docs_result:
            return []

        chain_data = function_docs_result[0]
        function_ids = [call['target']['_id']
                        for call in chain_data.get('calls', [])]

        origin = chain_data.get('origin')
        if origin and origin.get('node_type') == 'function':
            function_ids.insert(0, origin['_id'])

        # 4. Find logs that share a chain_id across all these functions
        flat_logs = await self.repos.log_repo.find_logs_for_function_chain(
            function_ids,
            start_function_id=called_function_id,

        )

        # 5. Build the tree from the flat list of logs
        return LogTreeBuilder(flat_logs).build()

    async def get_unified_log_tree(self, node_id: str) -> List[LogTreeNode]:
        """Return a log tree for either a function ID or a call ID.

        If the ID matches a function, return its log tree. If it matches a
        call, return the call log tree. Otherwise, return an empty list.
        """
        node = await self.repos.nodes.get_by_id(node_id)
        if node is None:
            return []

        if node.node_type == "function":
            return await self.get_function_log(node.id)
        elif node.node_type == "call":
            return await self.get_call_log(node.id)

        return []

    async def create_batch(self, batch_params: List["RegisterLogsParams"]):

        log_docs = []
        log_edges = []
        func_edges = []

        for p in batch_params:
            print(p.timestamp)
            # Assuming 'p' is a dict or RegisterLogsParams object
            # Adapt this extraction based on your exact input format
            log_docs.append(LogNode(
                key=f"{p.id}",
                timestamp=p.timestamp,
                event_type=p.event_type,
                message=p.message,
                level_name=p.level_name,
                duration_ms=p.duration_ms,
                chain_id=p.chain_id,
                payload=p.payload,
                result=p.result,
                error=p.error,
            ))

            func_edges.append({
                "from_id": f"logs/{p.id}",
                "to_id": f"nodes/{p.function_id}",
            })
            if p.parent_log_id:
                log_edges.append({
                    "from_id": f"logs/{p.id}",
                    "to_id": f"logs/{p.parent_log_id}"
                })
            print(f"Log edge {p.id} -> {p.parent_log_id}")

        # 2. Bulk Insert Logs (One DB Call)
        # We get back objects with valid .id properties
        await self.repos.log_repo.create_batch(log_docs)

        await self.repos.log_repo.create_batch_edges(func_edges, "log_to_function")
        await self.repos.log_repo.create_batch_edges(log_edges, "log_to_log")

        # Emit logs:new socket events for unique function_ids
        try:
            unique_function_ids = set(
                p.function_id for p in batch_params if p.function_id)
            for function_id in unique_function_ids:
                project_id = await self._get_project_id_from_node(function_id)
                if project_id:
                    await self.socket_manager.emit_to_project(
                        project_id,
                        "logs:new",
                        {"node_id": function_id}
                    )
        except Exception as e:
            # Non-fatal: failure to emit socket event should not block log creation
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to emit logs:new socket events: {e}")

        return True

    async def _get_project_id_from_node(self, node_id: str) -> Optional[str]:
        """Get project_id from a node_id by traversing up the containment tree."""
        try:
            # Use ContainerService's method to resolve project
            from app.core.services.container_service import ContainerService
            container_service = ContainerService(self.repos)
            _, project_doc = await container_service._resolve_file_and_project(node_id)
            if project_doc:
                return project_doc.get("_id")
        except Exception:
            pass
        return None
