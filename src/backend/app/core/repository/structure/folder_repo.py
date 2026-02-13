
from datetime import datetime, timezone
from app.db.async_terminus_client import AsyncClient
from app.core.model.nodes import FolderNode
from app.core.model.schemas import FolderSchema
from app.db.async_terminus_client import WOQLQuery as WQ
from app.db.schema.schema import WOQLSchema


class FolderRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, new_folder: FolderNode, project_db_name: str):

        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        folder_schema = FolderSchema(
            _id=new_folder.id,
            name=new_folder.name,
            description=new_folder.description,
            qname=new_folder.qname,
            path=new_folder.path,
            folder_children=new_folder.folder_children,
            file_children=new_folder.file_children,
            structure_group=new_folder.structure_group,
            created_at=new_folder.created_at,
            updated_at=new_folder.updated_at,
        )

        await self.client.insert_document(folder_schema, commit_msg=f"Creating folder {new_folder.name}")
        if current_db:
            await self.client.set_db(current_db)
        return folder_schema.to_pydantic()

    async def get_by_id(self, folder_id: str, project_db_name: str):
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

        folder = FolderNode(
            id=folder_raw["@id"],
            name=folder_raw["name"],
            description=folder_raw["description"],
            qname=folder_raw["qname"],
            path=folder_raw["path"],
            folder_children=folder_raw.get("folder_children", set()),
            file_children=folder_raw.get("file_children", set()),
            structure_group=folder_raw.get("structure_group", set()),
            created_at=folder_raw["created_at"],
            updated_at=folder_raw["updated_at"],
        )
        return folder

    async def delete(self, folder_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            # await self.client.delete_document(folder_id, commit_msg=f"Deleting folder {folder_id}")
            print(f"deleting folder {folder_id}")
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

    async def update(self, folder: FolderNode, project_db_name: str):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_folder = await self.get_by_id(folder.id, project_db_name)
        if not existing_folder:
            return None

        folder_schema = FolderSchema.from_pydantic(folder)
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

    async def get_children(self, folder_id: str, child_type: list[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None
        if len(child_type) == 0:
            filed_name = "(folder_children|file_children|structure_group)"
        else:
            filed_name = "|".join(child_type)

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
                if child_raw["@type"] == "FolderSchema":
                    folder = FolderNode.from_raw_dict(child_raw)
                    children.append(folder)
            # print(f"children {children}")
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
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", filed_name, item_id)
                    .delete_triple("v:parent", filed_name, item_id)
                ),
                WQ().add_triple(new_parent_id, filed_name, item_id)
            )
            result = await self.client.query(query, commit_msg=f"Moving item {item_id} to {new_parent_id}")

            return True
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
