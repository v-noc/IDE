from datetime import datetime, timezone
from typing import List, Tuple, Union
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import FolderNode
from app.core.model.schemas import FolderSchema
from app.db.async_terminus_client import WOQLQuery as WQ
from app.db.schema.schema import WOQLSchema
from app.core.repository.utils import (
    parse_structure_child,
    build_path_field_name,
    STRUCTURE_FIELDS,
)


class FolderRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, new_folder: Union[FolderNode, List[FolderNode]], project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        folder_schemas = []
        commit_msg = "Creating folders"
        if isinstance(new_folder, FolderNode):
            folder_schemas.append(FolderSchema.from_pydantic(new_folder))
            commit_msg = f"Creating folder {new_folder.name}"
        else:
            folder_schemas = [FolderSchema.from_pydantic(
                folder) for folder in new_folder]
            commit_msg = f"Creating folders {', '.join([folder.name for folder in new_folder])}"
        await self.client.insert_document(folder_schemas, commit_msg=commit_msg)
        if current_db:
            await self.client.set_db(current_db)
        if raw:
            return folder_schemas
        if len(folder_schemas) == 1:
            return folder_schemas[0].to_pydantic()
        return [folder_schema.to_pydantic() for folder_schema in folder_schemas]

    async def get_by_id(self, folder_id: str, project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            folder_raw = await self.client.get_document(folder_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

        if raw:
            return folder_raw
        return FolderNode.from_raw_dict(folder_raw)

    async def get_by_ids(self, folder_ids: List[str], project_db_name: str, raw: bool = False):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            folder_raw = await self.client.get_documents(folder_ids)
        except Exception as e:
            print(e)
            return []
        finally:
            if current_db:
                await self.client.set_db(current_db)
        if raw:
            return folder_raw
        return [FolderNode.from_raw_dict(folder_raw) for folder_raw in folder_raw]

    async def delete(self, folder_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            # await self.client.delete_document(folder_id, commit_msg=f"Deleting folder {folder_id}")

            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "folder_children", folder_id)
                    .delete_triple("v:parent", "folder_children", folder_id)
                ),
                WQ().delete_document(folder_id)
            )
            await self.client.query(query, commit_msg=f"Deleting folder {folder_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def delete_batch(self, folder_ids: List[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            # await self.client.delete_document(folder_id, commit_msg=f"Deleting folder {folder_id}")

            query = WQ().member("v:folder_id", folder_ids).woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "folder_children", "v:folder_id")
                    .delete_triple("v:parent", "folder_children", "v:folder_id")
                ),
                WQ().delete_document("v:folder_id")
            )
            await self.client.query(query, commit_msg=f"Deleting folders {', '.join(folder_ids)}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, folder: FolderNode, project_db_name: str):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_folder = await self.get_by_id(folder.id, project_db_name, raw=True)
        if not existing_folder:
            return None

        folder_schema = FolderSchema.from_pydantic(folder)

        folder_schema.folder_children = existing_folder.get(
            "folder_children", set())
        folder_schema.file_children = existing_folder.get(
            "file_children", set())
        folder_schema.structure_group = existing_folder.get(
            "structure_group", set())

        folder_schema.documents = existing_folder.get("documents", set())
        folder_schema.theme_config = existing_folder.get("theme_config")

        folder_schema.updated_at = datetime.now(timezone.utc)

        try:
            await self.client.update_document(folder_schema, commit_msg=f"Updating folder {folder.id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return folder_schema.to_pydantic()

    async def update_batch(self, folders: List[FolderNode], project_db_name: str):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_folders = await self.get_by_ids([folder.id for folder in folders], project_db_name, raw=True)
        if not existing_folders:
            return None
        folder_schemas = []
        for existing_folder, folder in zip(existing_folders, folders):

            folder_schema = FolderSchema.from_pydantic(folder)

            folder_schema.folder_children = existing_folder.get(
                "folder_children", set())
            folder_schema.file_children = existing_folder.get(
                "file_children", set())
            folder_schema.structure_group = existing_folder.get(
                "structure_group", set())

            folder_schema.documents = existing_folder.get("documents", set())
            folder_schema.theme_config = existing_folder.get("theme_config")

            folder_schema.updated_at = datetime.now(timezone.utc)
            folder_schemas.append(folder_schema)

        if len(folder_schemas) != len(folders):
            return None
        try:
            await self.client.update_document(folder_schemas, commit_msg=f"Updating folder {folder.id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def get_children(self, folder_id: str, child_type: list[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = build_path_field_name(child_type, STRUCTURE_FIELDS)

        try:
            query = (
                WQ()
                .select("v:child_doc")
                .woql_and(
                    WQ().eq("v:start", folder_id)
                    .path("v:start", f"{filed_name}+", "v:child")
                    .read_document("v:child", "v:child_doc")
                )
            )
            result = await self.client.query(query)
            children = []

            for child_raw in [row["child_doc"] for row in result["bindings"]]:
                node = parse_structure_child(child_raw)
                if node is not None:
                    children.append(node)
            return children
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def get_parent(self, item_id: str, child_type: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        filed_name = None
        match child_type:
            case "folder":
                filed_name = "folder_children"
            case "file":
                filed_name = "file_children"
            case "structure_group":
                filed_name = "structure_group"
            case _:
                return None
        if not filed_name:
            raise ValueError(f"Invalid child type: {child_type}")

        try:
            query = (
                WQ()
                .select("v:parent_doc")
                .woql_and(
                    WQ()
                    .triple("v:parent", filed_name, "v:item")
                    .eq("v:item", item_id)
                    .read_document("v:parent", "v:parent_doc")
                )
            )
            result = await self.client.query(query)
            return [row["parent_doc"] for row in result["bindings"]]
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def move_item(self, new_parent_id: str, item_id: str,  child_type: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None

        match child_type:
            case "folder":
                filed_name = "folder_children"
            case "file":
                filed_name = "file_children"
            case "structure_group":
                filed_name = "structure_group"
            case _:
                return None

        if not filed_name:
            raise ValueError(f"Invalid child type: {child_type}")

        try:
            current_time = datetime.now(timezone.utc)
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", filed_name, item_id)
                    .delete_triple("v:parent", filed_name, item_id)
                    .update_triple("v:parent", "updated_at", current_time)
                ),
                WQ().add_triple(new_parent_id, filed_name, item_id)
                .update_triple(new_parent_id, "updated_at", current_time)
            )
            await self.client.query(query, commit_msg=f"Moving item {item_id} to {new_parent_id}")

            return True
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def move_batch(self, moves: List[Tuple[str, str, str]], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        parsed_data = {}
        # item_id, parent_id, child_type
        for move in moves:
            item_id, parent_id, child_type = move
            if parent_id not in parsed_data:
                parsed_data[parent_id] = {
                    "folder_children": set(),
                    "file_children": set(),
                    "structure_group": set(),
                }
            if child_type == "folder":
                parsed_data[parent_id]["folder_children"].add(item_id)
            elif child_type == "file":
                parsed_data[parent_id]["file_children"].add(item_id)
            elif child_type == "structure_group":
                parsed_data[parent_id]["structure_group"].add(item_id)
            else:
                raise ValueError(f"Invalid child type: {child_type}")
        try:
            #

            current_time = datetime.now(timezone.utc)
            queries = []
            for data in parsed_data:
                for filed in parsed_data[data]:
                    if len(parsed_data[data][filed]) > 0:
                        # construct query
                        query = WQ().member("v:item", list(parsed_data[data][filed])).woql_and(
                            WQ().opt(
                                WQ().triple("v:parent", filed, "v:item")
                                .delete_triple("v:parent", filed, "v:item")
                            ),
                            WQ().add_triple(data, filed, "v:item")
                            .update_triple(data, "updated_at", current_time)
                        )
                        queries.append(query)
            query = WQ().woql_or(*queries)
            await self.client.query(query, commit_msg=f"Moving items to {', '.join([parent_id for parent_id in parsed_data.keys()])}")
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def get_all_folders(self, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            result = await self.client.get_all_documents(doc_type=FolderSchema.__name__)
            folders = []
            for folder_raw in result:
                node = FolderNode.from_raw_dict(folder_raw)
                if node is not None:
                    folders.append(node)
            return folders
        except Exception as e:
            print(e)
            return []
        finally:
            if current_db:
                await self.client.set_db(current_db)
