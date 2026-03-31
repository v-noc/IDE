
from datetime import datetime, timezone
import uuid
from typing import Literal, List, Tuple
from app.core.model.nodes import CallNode
from app.db.context import ProjectUoW


class CallService():
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

    async def create(
        self,
        name: str,
        qname: str,
        description: str,
        target_id: str,

    ):
        call = CallNode(
            id=f"CallSchema/{str(uuid.uuid4())}",
            name=name,
            qname=qname,
            description=description,
            target_function=target_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        new_call = await self.repos.call_repo.create(call)

        return new_call

    async def create_batch(self, calls: List[CallNode]):
        return await self.repos.call_repo.create(calls)

    async def get(self, call_id: str):
        return await self.repos.call_repo.get_by_id(call_id)

    async def update(self, call: CallNode):
        return await self.repos.call_repo.update(call)

    async def delete(self, call_id: str):
        return await self.repos.call_repo.delete(call_id)

    async def move_batch(self, moves: List[Tuple[str, str, str]]):
        return await self.repos.call_repo.move_batch(moves)

    async def batch_delete(self, call_ids: List[str]):
        return await self.repos.call_repo.batch_delete_calls(call_ids)

    async def add_call(self, parent_call_id: str, call_id: str):
        return await self.repos.call_repo.move_item(
            parent_call_id,
            call_id,
            "call",
        )

    async def get_children(self, call_id: str, child_type: list[Literal["call", "call_group"]] = []):
        return await self.repos.call_repo.get_children(call_id, child_type)

    async def get_direct_call_children(self, call_site_id: str, child_type: str):
        """
        Get direct call-node children of a given parent (call/group/container).

        This only returns vertices whose node_type == \"call\" at depth 1,
        ignoring groups and deeper descendants.
        """
        children = await self.repos.call_repo.get_direct_children(
            call_site_id, child_type
        )

        return children

    async def get_code(self, call_id: str):
        call = await self.repos.call_repo.get_by_id(call_id)
        if not call:
            return None

        file_doc, project_doc = await self._resolve_file_and_project(call.id)
        if not file_doc or not project_doc:
            return None

        abs_path = await self._build_abs_file_path(
            project_doc.get("path"),
            file_doc.get("path"),
        )
        code = await self._extract_code_from_file(
            abs_path,
            call.position,
        )

        return {
            "id": call.id,
            "name": call.name,
            "node_type": call.node_type,
            "qname": call.qname,
            "file_path": file_doc.get("path"),
            "file_name": file_doc.get("name"),
            "position": call.position.model_dump(),
            "code": code,
        }

    async def flush_batch(
        self,
        inserts: List[CallNode],
        deletes: List[str],
        moves: List[Tuple[str, str, str]],
    ):
        return await self.repos.call_repo._flush_batch_combined(
            inserts, deletes, moves
        )

    async def get_call_with_parent_and_target(self, parent_id: str, target_id: str):
        # Note: repository expects (target_id, parent_id)
        return await self.repos.call_repo.find_call_by_target_parent(
            target_id,
            parent_id,
        )

    async def get_call_parent_chain(self, call_id: str):
        return await self.repos.call_repo.get_call_chain(call_id)
