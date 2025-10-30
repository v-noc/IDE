from fastapi import APIRouter
from . import health
from .core.projects import crud as project_crud
from .core import container
from .core import code_element
from .core import logger as logger_api
from .core import documents as documents_api
from .core import calls as calls_api
from .core import group as group_api
# from .core import base as core_base
router = APIRouter()


@router.get("/")
def get_root():
    return {"Hello": "World"}


router.include_router(health.router, prefix="/health", tags=["health"])


router.include_router(project_crud.router,
                      prefix="/projects", tags=["projects"])

router.include_router(
    container.router, prefix="/containers", tags=["containers"])

router.include_router(
    code_element.router, prefix="/code-elements", tags=["code-elements"]
)

router.include_router(logger_api.router, prefix="/logs", tags=["logs"])

router.include_router(documents_api.router,
                      prefix="/documents", tags=["documents"])

router.include_router(calls_api.router, prefix="/calls", tags=["calls"])

router.include_router(group_api.router, prefix="/groups", tags=["groups"])
