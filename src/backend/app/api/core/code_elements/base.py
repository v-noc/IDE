from fastapi import APIRouter, HTTPException, Depends
from app.core.manager import CodeGraphManager
from app.core.code_elements import to_domain_element
from app.core.file import File
from app.core.virtual_folder import VirtualFolder
router = APIRouter()

def get_manager() -> CodeGraphManager:
    return CodeGraphManager()


@router.get("/nodes/{element_id}/code")
def get_code_from_element(
    element_id: str,
    manager: CodeGraphManager = Depends(get_manager),
) -> dict:
    """
    Gets the code text for a specific code element (function or class)
    by its ID. Returns the code text along with metadata about the element.
    """
    # Get the code element node
    element_node = manager.get_node(element_id)
    if not element_node:
        raise HTTPException(
            status_code=404, detail="Code element not found"
        )

    # Convert to domain element (function/class)
    element = to_domain_element(element_node)
    if not element:
        node_type = getattr(element_node, "node_type", None)
        if node_type == "file":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Use the file-code endpoint for file content: "
                    "/code-elements/nodes/{id}/file-code"
                ),
            )
        if node_type == "virtual_folder":
            # If a virtual folder links to a function/class we still support it
            vf = VirtualFolder(element_node)
            link_edge = vf.get_linked_element_edge()
            if not link_edge:
                raise HTTPException(
                    status_code=404,
                    detail="Virtual folder has no linked element",
                )
            linked_node = manager.get_node(link_edge.to_id)
            if not linked_node:
                raise HTTPException(
                    status_code=404,
                    detail="Linked element not found",
                )
            linked_element = to_domain_element(linked_node)
            if not linked_element:
                # If linked to a file, direct callers to file-code route
                if getattr(linked_node, "node_type", None) == "file":
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Virtual folder links to a file. Use the "
                            "file-code endpoint: /code-elements/nodes/"
                            "{id}/file-code"
                        ),
                    )
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Linked element must be a function or class to "
                        "fetch a code segment"
                    ),
                )
            # Return the linked function/class code segment
            try:
                parent_file = linked_element.get_parent_file()
                code_text = parent_file.get_text(linked_element.position)
                return {
                    "element_id": linked_element.id,
                    "element_name": linked_element.name,
                    "element_type": linked_node.node_type,
                    "qname": linked_element.qname,
                    "code": code_text,
                    "file_path": parent_file.path,
                    "file_name": parent_file.name,
                    "position": {
                        "line_no": linked_element.position.line_no,
                        "col_offset": linked_element.position.col_offset,
                        "end_line_no": getattr(
                            linked_element.position, 'end_line_no', None
                        ),
                        "end_col_offset": getattr(
                            linked_element.position, 'end_col_offset', None
                        ),
                    },
                }
            except FileNotFoundError:
                raise HTTPException(
                    status_code=404,
                    detail="Source file not found",
                )
        # Unsupported type
        raise HTTPException(
            status_code=400,
            detail="Element is not a function or class",
        )

    try:
        # Get the parent file
        parent_file = element.get_parent_file()
        # Get the code text using the element's position
        code_text = parent_file.get_text(element.position)
        return {
            "element_id": element_id,
            "element_name": element.name,
            "element_type": element_node.node_type,
            "qname": element.qname,
            "code": code_text,
            "file_path": parent_file.path,
            "file_name": parent_file.name,
            "position": {
                "line_no": element.position.line_no,
                "col_offset": element.position.col_offset,
                "end_line_no": getattr(
                    element.position, 'end_line_no', None
                ),
                "end_col_offset": getattr(
                    element.position, 'end_col_offset', None
                ),
            },
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Source file not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading code: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


@router.get("/nodes/{file_id}/file-code")
def get_full_code_from_file(
    file_id: str,
    manager: CodeGraphManager = Depends(get_manager),
) -> dict:
    """
    Returns full source code for:
    - a file node by its ID, or
    - a virtual folder that is linked to a file
    """
    node_model = manager.get_node(file_id)
    if not node_model:
        raise HTTPException(status_code=404, detail="Node not found")

    node_type = getattr(node_model, "node_type", None)

    # Case 1: Direct file id
    if node_type == "file":
        target_file_node = node_model
    # Case 2: Virtual folder linked to a file
    elif node_type == "virtual_folder":
        vf = VirtualFolder(node_model)
        link_edge = vf.get_linked_element_edge()
        if not link_edge:
            raise HTTPException(
                status_code=404,
                detail="Virtual folder has no linked element",
            )
        linked_node = manager.get_node(link_edge.to_id)
        if not linked_node:
            raise HTTPException(
                status_code=404,
                detail="Linked element not found",
            )
        if getattr(linked_node, "node_type", None) != "file":
            raise HTTPException(
                status_code=400,
                detail="Virtual folder is not linked to a file",
            )
        target_file_node = linked_node
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                "Node must be a file or a virtual folder linked to a file"
            ),
        )

    try:
        file = File(target_file_node)
        project = file.get_project()
        full_path = f"{project.path}/{file.path}"
        try:
            with open(full_path, "r") as f:
                code_text = f.read()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Source file not found",
            )

        return {
            "file_id": file.id,
            "file_name": file.name,
            "file_path": file.path,
            "node_type": "file",
            "qname": target_file_node.qname,
            "code": code_text,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )

