from datetime import datetime, timezone
from typing import List, Tuple, Union
from app.core.model.nodes import FileNode
from app.core.model.schemas import FileSchema
from app.db.async_terminus_client import AsyncClient
from app.db.async_terminus_client import WOQLQuery as WQ
from app.core.repository.utils import build_path_field_name, parse_code_element_child, CODE_ELEMENT_FIELDS


class FileRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    async def create(self, file: List[Union[FileNode, List[FileNode]]], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        file_schemas = []
        commit_msg = "Creating files"
        if isinstance(file, FileNode):
            commit_msg = f"Creating file {file.name}"
            file_schemas.append(FileSchema.from_pydantic(file))
        else:
            commit_msg = f"Creating files {', '.join([file.name for file in file])}"
            file_schemas = [FileSchema.from_pydantic(file) for file in file]
        await self.client.insert_document(file_schemas, commit_msg=commit_msg)
        if current_db:
            await self.client.set_db(current_db)
        if len(file_schemas) == 1:
            return file_schemas[0].to_pydantic()
        return [file_schema.to_pydantic() for file_schema in file_schemas]

    async def get_children(self, file_id: str, child_type: list[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = build_path_field_name(child_type, CODE_ELEMENT_FIELDS)

        try:
            query = (
                WQ()
                .select("v:child_doc")
                .woql_and(
                    WQ().eq("v:start", file_id)
                    .path("v:start", f"{filed_name}+", "v:child")
                    .read_document("v:child", "v:child_doc")
                )
            )
            result = await self.client.query(query)
            children = []

            for child_raw in [row["child_doc"] for row in result["bindings"]]:
                node = parse_code_element_child(child_raw)
                if node is not None:
                    children.append(node)
            return children
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

    async def get_by_id(self, file_id: str, project_db_name: str, raw: bool = False):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            file_raw = await self.client.get_document(file_id)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

        if raw:
            return file_raw
        return FileNode.from_raw_dict(file_raw)

    async def get_by_ids(self, file_ids: List[str], project_db_name: str, raw: bool = False):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            files_raw = await self.client.get_documents(file_ids)
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)

        if raw:
            return files_raw
        return [FileNode.from_raw_dict(file_raw) for file_raw in files_raw]

    async def delete(self, file_id: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "file_children", file_id)
                    .delete_triple("v:parent", "file_children", file_id)
                ),
                WQ().delete_document(file_id)
            )
            await self.client.query(query, commit_msg=f"Deleting file {file_id}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def delete_batch(self, file_ids: List[str], project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            query = WQ().member("v:file_id", file_ids).woql_and(
                WQ().opt(
                    WQ().triple("v:parent", "file_children", "v:file_id")
                    .delete_triple("v:parent", "file_children", "v:file_id")
                ),
                WQ().delete_document("v:file_id")
            )
            await self.client.query(query, commit_msg=f"Deleting files {', '.join(file_ids[:5])}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def update(self, file: FileNode, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_file = await self.get_by_id(file.id, project_db_name, raw=True)
        if not existing_file:
            return None
        file_schema = FileSchema.from_pydantic(file)

        file_schema.call_children = existing_file.get("call_children", set())
        file_schema.call_group = existing_file.get("call_group", set())
        file_schema.class_children = existing_file.get("class_children", set())
        file_schema.function_children = existing_file.get(
            "function_children", set())
        file_schema.code_element_group = existing_file.get(
            "code_element_group", set())

        file_schema.updated_at = datetime.now(timezone.utc)
        try:
            await self.client.update_document(file_schema, commit_msg=f"Updating file {file.id}")
        except Exception as e:
            print(e)
            return None
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return file_schema.to_pydantic()

    async def update_batch(self, files: List[FileNode], project_db_name: str):
        current_db = None

        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        existing_files = await self.get_by_ids([folder.id for folder in files], project_db_name, raw=True)
        if not existing_files:
            return None
        file_schemas = []
        for existing_file, file in zip(existing_files, files):

            file_schema = FileSchema.from_pydantic(file)

            file_schema.call_children = existing_file.get(
                "call_children", set())
            file_schema.call_group = existing_file.get("call_group", set())
            file_schema.class_children = existing_file.get(
                "class_children", set())
            file_schema.function_children = existing_file.get(
                "function_children", set())
            file_schema.code_element_group = existing_file.get(
                "code_element_group", set())

            file_schema.documents = existing_file.get("documents", set())
            file_schema.theme_config = existing_file.get("theme_config")

            file_schema.updated_at = datetime.now(timezone.utc)
            file_schemas.append(file_schema)

        if len(file_schemas) != len(files):
            return None

        try:
            await self.client.update_document(file_schemas, commit_msg=f"Updating files {len(file_schemas)}")
        except Exception as e:
            print(e)
            return False
        finally:
            if current_db:
                await self.client.set_db(current_db)
        return True

    async def move_item(self, new_parent_id: str, item_id: str,  child_type: str, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)

        filed_name = None

        match child_type:
            case "function":
                filed_name = "function_children"
            case "class":
                filed_name = "class_children"
            case "call":
                filed_name = "call_children"
            case "code_element_group":
                filed_name = "code_element_group"
            case "call_group":
                filed_name = "call_group"
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
                    "function_children": set(),
                    "class_children": set(),
                    "call_children": set(),
                    "code_element_group": set(),
                    "call_group": set(),
                }
            if child_type == "function":
                parsed_data[parent_id]["function_children"].add(item_id)
            elif child_type == "class":
                parsed_data[parent_id]["class_children"].add(item_id)
            elif child_type == "call":
                parsed_data[parent_id]["call_children"].add(item_id)
            elif child_type == "code_element_group":
                parsed_data[parent_id]["code_element_group"].add(item_id)
            elif child_type == "call_group":
                parsed_data[parent_id]["call_group"].add(item_id)
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

    async def get_all_files(self, project_db_name: str):
        current_db = None
        if self.client.db != project_db_name:
            current_db = self.client.db
            await self.client.set_db(project_db_name)
        try:
            result = await self.client.get_all_documents(doc_type=FileSchema.__name__)
            files = []
            for file_raw in result:
                node = FileNode.from_raw_dict(file_raw)
                if node is not None:
                    files.append(node)
            return files
        except Exception as e:
            print(e)
            return []
        finally:
            if current_db:
                await self.client.set_db(current_db)
