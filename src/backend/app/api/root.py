from fastapi import APIRouter
from . import health
from .core.projects import crud as project_crud
from .core.folder import virtual_folders


router = APIRouter()


@router.get("/")
def get_root():
    return {"Hello": "World"}


router.include_router(
    health.router, prefix="/health", tags=["health"]
)
router.include_router(
    project_crud.router, prefix="/project", tags=["project"]
)
router.include_router(
    virtual_folders.router, tags=["virtual-folder"]
)
