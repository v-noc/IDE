from fastapi import APIRouter, HTTPException, Body
from app.models.properties import ThemeConfig
from app.db.collections import nodes
from app.models import properties as node_props


router = APIRouter()


@router.post("/{element_key}/update-node-theme")
def update_layout_metadata(
    element_key: str,
    layout_metadata: ThemeConfig,
):
    db_node = nodes.get(element_key)
    if not db_node:
        raise HTTPException(status_code=404, detail="Element not found")

    if db_node.properties is None:
        if getattr(db_node, "node_type", None) == "virtual_folder":
            db_node.properties = node_props.VirtualFolderProperties()
        elif getattr(db_node, "node_type", None) == "virtual_file":
            db_node.properties = node_props.VirtualFileProperties()
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Properties are missing for this node type and cannot be "
                    "auto-initialized."
                ),
            )

    db_node.properties.metaData = layout_metadata
    nodes.update(db_node)

    return nodes.get(element_key)


@router.post("/{element_key}/update-icon")
def update_icon(
    element_key: str,
    icon: str = Body(embed=True),
):
    db_node = nodes.get(element_key)
    if not db_node:
        raise HTTPException(status_code=404, detail="Element not found")

    db_node.icon = icon
    nodes.update(db_node)

    return nodes.get(element_key)