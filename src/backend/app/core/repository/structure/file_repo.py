# from typing import Dict, Any, List
# from ..base.base_node_repo import BaseNodeRepository
# from app.core.model.nodes import FileNode
# from arangoasync.database import AsyncDatabase
from app.db.async_terminus_client import AsyncClient


# class FileRepo(BaseNodeRepository[FileNode]):
#     def __init__(self, db: AsyncDatabase):
#         super().__init__(db, "nodes", FileNode)

#     async def get_project_files(self, project_id: str) -> List[Dict[str, Any]]:
#         """
#         Returns a list of file details (path, id, checksum) belonging to the specific project.
#         Uses graph traversal to ensure we only get nodes connected to this project.
#         """
#         query = """
#             FOR v, e, p IN 1..100 OUTBOUND @project_id @@contains_collection
#                 OPTIONS { order: "bfs", uniqueVertices: "global" }
#                 FILTER v.node_type == "file"
#                 // Optional: Double check path just in case, but graph logic is primary
#                 RETURN {
#                     path: v.path,
#                     id: v._key,
#                     checksum: v.hash
#                 }
#         """
#         cursor = await self.db.aql.execute(
#             query,
#             bind_vars={
#                 "project_id": project_id,
#                 "@contains_collection": "contains_edges"
#             }
#         )
#         return [doc async for doc in cursor]

class FileRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    def get_file_by_id(self, file_id: str):
        pass

    def get_file_by_path(self, path: str):
        pass

    def get_file_by_qname(self, qname: str):
        pass

    def get_children(self, folder_id: str):
        pass

    def get_direct_children(self, file_id: str):
        pass

    def move_item(self, item_id: str, new_parent_id: str, child_type: str):
        pass

    def add_child(self, parent_id: str, child_id: str, child_type: str):
        pass

    def remove_child(self, parent_id: str, child_id: str, child_type: str):
        pass

    def create_file(self, parent_id: str, name: str, description: str):
        pass

    def update_file(self, file_id: str, name: str, description: str):
        pass

    def delete_file(self, file_id: str):
        pass
