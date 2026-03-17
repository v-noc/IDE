from datetime import datetime, timezone
import os
import uuid
from typing import Optional

from app.core.model.schemas.code_element_schema import PlayGroundSchema
from app.core.sandbox.code_run import CodeResponse, CodeRunner
from app.db.context import ProjectUoW


class PlayGroundService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.repos = self.uow.get_project_repos()

    @staticmethod
    def _owner_count(
        owner_function: Optional[str],
        owner_class: Optional[str],
        owner_file: Optional[str],
        owner_folder: Optional[str],
    ) -> int:
        return len(
            [
                owner
                for owner in [owner_function, owner_class, owner_file, owner_folder]
                if owner
            ]
        )

    async def create_playground(
        self,
        name: str,
        description: str,
        relative_path: str,
        code: str,
        executable_path: Optional[str] = None,
        examples_path: Optional[str] = None,
        command_prefix: Optional[str] = None,
        filename: Optional[str] = None,
        owner_function: Optional[str] = None,
        owner_class: Optional[str] = None,
        owner_file: Optional[str] = None,
        owner_folder: Optional[str] = None,
    ) -> Optional[dict]:
        owner_count = self._owner_count(
            owner_function, owner_class, owner_file, owner_folder
        )
        if owner_count == 0:
            raise ValueError(
                "One owner is required: owner_function, owner_class, owner_file, or owner_folder"
            )
        if owner_count > 1:
            raise ValueError("Playground can only belong to one owner")

        now = datetime.now(timezone.utc)
        playground_id = f"PlayGroundSchema/{uuid.uuid4()}"
        playground = PlayGroundSchema(
            _id=playground_id,
            name=name,
            description=description,
            relative_path=relative_path,
            code=code,
            executable_path=executable_path,
            examples_path=examples_path,
            command_prefix=command_prefix,
            filename=filename,
            owner_function=owner_function,
            owner_class=owner_class,
            owner_file=owner_file,
            owner_folder=owner_folder,
            created_at=now,
            updated_at=now,
        )
        created = await self.repos.play_ground_repo.create(playground)
        if not created:
            return None
        return await self.repos.play_ground_repo.get_by_id(playground_id)

    async def get_playground_by_id(self, playground_id: str) -> Optional[dict]:
        return await self.repos.play_ground_repo.get_by_id(playground_id)

    async def update_playground(
        self,
        playground_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        relative_path: Optional[str] = None,
        code: Optional[str] = None,
        executable_path: Optional[str] = None,
        examples_path: Optional[str] = None,
        command_prefix: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Optional[dict]:
        existing = await self.repos.play_ground_repo.get_by_id(playground_id)
        if not existing:
            return None

        now = datetime.now(timezone.utc)
        updated = PlayGroundSchema(
            _id=existing.get("@id", playground_id),
            name=existing.get("name", "") if name is None else name,
            description=existing.get("description", "")
            if description is None
            else description,
            relative_path=existing.get("relative_path", "")
            if relative_path is None
            else relative_path,
            code=existing.get("code", "") if code is None else code,
            executable_path=existing.get("executable_path")
            if executable_path is None
            else executable_path,
            examples_path=existing.get("examples_path")
            if examples_path is None
            else examples_path,
            command_prefix=existing.get("command_prefix")
            if command_prefix is None
            else command_prefix,
            filename=existing.get("filename") if filename is None else filename,
            owner_function=existing.get("owner_function"),
            owner_class=existing.get("owner_class"),
            owner_file=existing.get("owner_file"),
            owner_folder=existing.get("owner_folder"),
            created_at=existing.get("created_at", now),
            updated_at=now,
        )
        ok = await self.repos.play_ground_repo.update(updated)
        if not ok:
            return None
        return await self.repos.play_ground_repo.get_by_id(playground_id)

    async def delete_playground(self, playground_id: str) -> bool:
        return await self.repos.play_ground_repo.delete(playground_id)

    async def get_by_owner_function_id(self, owner_function_id: str) -> list[dict]:
        return await self.repos.play_ground_repo.get_by_owner_function_id(owner_function_id)

    async def get_by_owner_class_id(self, owner_class_id: str) -> list[dict]:
        return await self.repos.play_ground_repo.get_by_owner_class_id(owner_class_id)

    async def get_by_owner_file_id(self, owner_file_id: str) -> list[dict]:
        return await self.repos.play_ground_repo.get_by_owner_file_id(owner_file_id)

    async def get_by_owner_folder_id(self, owner_folder_id: str) -> list[dict]:
        return await self.repos.play_ground_repo.get_by_owner_folder_id(owner_folder_id)

    async def run_code(self, playground_id: str) -> CodeResponse:
        playground = await self.repos.play_ground_repo.get_by_id(playground_id)
        if not playground:
            raise ValueError("Playground not found")

        project_node = self.uow.project
        if project_node is None:
            raise ValueError("Project not found")

        project_path = os.path.abspath(getattr(project_node, "path", ""))
        if not project_path:
            raise ValueError("Project path is missing")

        return CodeRunner().run_code(
            project_root_path=project_path,
            python_executable=playground.get("executable_path"),
            code=playground.get("code", ""),
            examples_path=playground.get("examples_path"),
            command_prefix=playground.get("command_prefix"),
            filename=playground.get("filename"),
        )
