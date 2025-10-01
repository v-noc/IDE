from fastapi import APIRouter
from . import health
from .core.projects import crud as project_crud
# from .core import base as core_base
router = APIRouter()


@router.get("/")
def get_root():
    return {"Hello": "World"}


router.include_router(
    health.router, prefix="/health", tags=["health"]
)
router.include_router(
    project_crud.router, prefix="/projects", tags=["projects"]
)

# router.include_router(
#     core_base.router, prefix="/core", tags=["core"]
# )
