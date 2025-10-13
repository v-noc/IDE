from typing import Optional, TYPE_CHECKING

from app.core.repository import Repositories
from app.core.model.logs import LogNode
from app.core.model.edges import LogToFunctionEdge, LogToLogEdge

if TYPE_CHECKING:
    from app.api.json_rpc.schemas import RegisterLogsParams

from app.core.builder.log_tree_builder import LogTreeBuilder


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
            )
        )

        self._link_to_parent_log(created, function_id,
                                 parent_function_id, params.chain_id)

        return created

    def _link_to_parent_log(self, created_log: LogNode, function_id: str, parent_function_id: Optional[str], chain_id: Optional[str]):
        if not chain_id:
            return

        parent_log = None

        # If not an enter event, first try to find parent within the same function
        if created_log.event_type != "enter":
            parent_log = self.repos.log_repo.find_enter_log(
                function_id=function_id,
                chain_id=chain_id,
            )

        # If it's an enter event, or no parent was found in the same function, check the parent function
        if not parent_log and parent_function_id:
            parent_log = self.repos.log_repo.find_enter_log(
                function_id=parent_function_id,
                chain_id=chain_id,
            )

        if parent_log:
            self.repos.log_to_log_edges.create(
                LogToLogEdge(
                    from_id=created_log.id,
                    to_id=parent_log.id,
                )
            )

    def get_parent_log(self, log_id: str):
        return self.repos.log_repo.find_parent_log(log_id)

    def get_function_log(self, function_id: str):
        flat_logs = self.repos.log_repo.find_function_log(function_id)
        return LogTreeBuilder(flat_logs).build()

    def get_log_containment_tree(self, log_id: str):
        """Gets all descendant logs for a given log ID and builds a tree."""
        flat_descendants = self.repos.log_repo.get_containment_tree(log_id)

        root_log = self.repos.log_repo.get_by_id(log_id)
        if not root_log:
            return []

        flat_list = [{"vertex": root_log.model_dump(
            by_alias=True), "parent_id": None}]
        flat_list.extend(flat_descendants)

        return LogTreeBuilder(flat_list).build()

    def get_call_log(self, call_id: str):
        # 1. Get the upward call chain, including the origin
        chain_info = self.repos.call_repo.find_upward_call_chain(call_id)
        if not chain_info:
            return []

        data = chain_info[0]
        origin = data.get("origin")
        calls = data.get("calls", [])

        if not origin:
            return []

        # 2. Collect all relevant function/method IDs
        # The 'origin' is a function, and each 'call' has a 'target' which is a function
        function_ids = [origin["_id"]]
        for call_item in calls:
            target = call_item.get("target")
            if target:
                function_ids.append(target["_id"])

        # 3. Find logs that share a chain_id across all these functions
        flat_logs = self.repos.log_repo.find_logs_for_function_chain(
            function_ids)

        # 4. Build the tree from the flat list of logs
        return LogTreeBuilder(flat_logs).build()
