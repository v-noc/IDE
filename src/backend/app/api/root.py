from fastapi import APIRouter
from . import health
from .core.projects import crud as project_crud
from .core import container
from .core import code_element
from .core import logger as logger_api
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

router.include_router(
    container.router, prefix="/containers", tags=["containers"]
)

router.include_router(
    code_element.router, prefix="/code-elements", tags=["code-elements"]
)

router.include_router(
    logger_api.router, prefix="/logs", tags=["logs"]
)
