from fastapi import APIRouter, HTTPException, Depends
from app.core.manager import CodeGraphManager
from app.core.code_elements import to_domain_element
from app.core.file import File

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

    # Convert to domain element
    element = to_domain_element(element_node)
    if not element:
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
            }
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
    Gets the full source code for a file node by its ID.
    """
    file_node = manager.get_node(file_id)
    if not file_node:
        raise HTTPException(status_code=404, detail="File not found")
    if getattr(file_node, "node_type", None) != "file":
        raise HTTPException(status_code=400, detail="Node is not a file")

    try:
        file = File(file_node)
        project = file.get_project()
        full_path = f"{project.path}/{file.path}"
        try:
            with open(full_path, "r") as f:
                code_text = f.read()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="Source file not found"
            )

        return {
            "file_id": file_id,
            "file_name": file.name,
            "file_path": file.path,
            "node_type": file_node.node_type,
            "qname": file_node.qname,
            "code": code_text,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
