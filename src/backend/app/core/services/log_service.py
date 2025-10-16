from typing import Optional, TYPE_CHECKING, List

from app.core.repository import Repositories
from app.core.model.logs import LogNode
from app.core.model.edges import LogToFunctionEdge, LogToLogEdge
from app.core.schemas.log_tree import LogTreeNode

if TYPE_CHECKING:
    from app.api.json_rpc.schemas import RegisterLogsParams

from app.core.builder.log_tree_builder import LogTreeBuilder


class LogService:
    def __init__(self, repos: Repositories):
        self.repos = repos

    def create(
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

        self._link_to_parent_log(
            created, function_id, parent_function_id, params.chain_id
        )

        return created

    def _link_to_parent_log(
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
            parent_log = self.repos.log_repo.find_enter_log(
                function_id=function_id,
                chain_id=chain_id,
            )

        # If it's an enter event, or no parent was found in the same function,
        # check the parent function
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

    def get_call_log(self, call_id: str) -> List[LogTreeNode]:
        # 1. Find the function that was called
        callees = self.repos.call_repo.get_target(call_id)
        if not callees:
            return []
        called_function_id = callees.id

        # 2. Find the full function call chain
        function_docs_result = self.repos.call_repo.find_upward_call_chain(
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
        flat_logs = self.repos.log_repo.find_logs_for_function_chain(
            function_ids,
            start_function_id=called_function_id,

        )

        # 5. Build the tree from the flat list of logs
        return LogTreeBuilder(flat_logs).build()

    def find_function_log(self, function_id: str):
        flat_logs = self.repos.log_repo.find_function_log(function_id)

        return LogTreeBuilder(flat_logs).build()

    def get_unified_log_tree(self, node_id: str) -> List[LogTreeNode]:
        """Return a log tree for either a function ID or a call ID.

        If the ID matches a function, return its log tree. If it matches a
        call, return the call log tree. Otherwise, return an empty list.
        """
        # Try function first
        fn = self.repos.function_repo.get_by_id(node_id)
        if fn is not None:
            return self.find_function_log(fn.id)

        # Then try call
        call = self.repos.call_repo.get_by_id(node_id)
        if call is not None:
            return self.get_call_log(call.id)

        return []
