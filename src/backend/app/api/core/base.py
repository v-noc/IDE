# from fastapi import APIRouter, HTTPException, Body
# from app.core.model.properties import ThemeConfig
# # from app.db.collections import nodes

# from pydantic import BaseModel, Field
# from typing import Optional


# router = APIRouter()


# class BasicInfo(BaseModel):
#     name: str = Field(
#         ...,
#         description="The name of the node",
#         min_length=1,
#         max_length=100,
#     )
#     description: Optional[str] = Field(
#         None,
#         description="The description of the node",
#     )


# @router.post("/nodes/{element_key}/update-node-theme")
# def update_node_theme(
#     element_key: str,
#     theme: ThemeConfig,
# ):
#     # db_node = nodes.get(element_key)
#     # if not db_node:
#     #     raise HTTPException(status_code=404, detail="Element not found")

#     # if db_node.properties is None:
#     #     if getattr(db_node, "node_type", None) == "virtual_folder":
#     #         db_node.properties = node_props.VirtualFolderProperties()
#     #     elif getattr(db_node, "node_type", None) == "virtual_file":
#     #         db_node.properties = node_props.VirtualFileProperties()
#     #     else:
#     #         raise HTTPException(
#     #             status_code=400,
#     #             detail=(
#     #                 "Properties are missing for this node type and "
#     #                 "cannot be auto-initialized."
#     #             ),
#     #         )

#     # Only apply values provided by client; do not set defaults
#     existing = db_node.properties.metaData
#     updates = theme.model_dump(exclude_unset=True)

#     if existing is None:
#         if not updates:
#             return nodes.get(element_key)
#         # Create a new ThemeConfig with only provided fields, others remain None
#         merged = ThemeConfig(**updates)
#     else:
#         base_dict = existing.model_dump()
#         base_dict.update({k: v for k, v in updates.items() if v is not None})
#         merged = ThemeConfig(**base_dict)

#     db_node.properties.metaData = merged
#     nodes.update(db_node)

#     return nodes.get(element_key)


# @router.post("/nodes/{element_key}/update-icon")
# def update_icon(
#     element_key: str,
#     icon: str = Body(embed=True),
# ):
#     db_node = nodes.get(element_key)
#     if not db_node:
#         raise HTTPException(status_code=404, detail="Element not found")

#     db_node.icon = icon
#     nodes.update(db_node)

#     return nodes.get(element_key)


# @router.post("/nodes/{element_key}/update-basic-info")
# def update_basic_info(
#     element_key: str,
#     basic_info: BasicInfo,
# ):
#     db_node = nodes.get(element_key)
#     if not db_node:
#         raise HTTPException(status_code=404, detail="Element not found")

#     db_node.name = basic_info.name
#     db_node.description = basic_info.description
#     nodes.update(db_node)

#     return nodes.get(element_key)
