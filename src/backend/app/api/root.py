from fastapi import APIRouter
from . import health
from .v1 import project_routes
from .v1 import code_routes
from .v1 import logger_routes
from .v1 import document_routes
from .v1 import test_routes
from .v1 import play_ground_routes
from .v1.versioning import router as versioning_router
from .v1 import container_routes
# from .v1 import call_routes
from .v1 import group_routes
from .v1 import conversation_routes
from app.walkthrough import routes as walkthrough_routes

router = APIRouter()


@router.get("/")
def get_root():
    return {"Hello": "World"}


router.include_router(health.router, prefix="/health", tags=["health"])


router.include_router(project_routes.router,
                      prefix="/projects", tags=["projects"])

# router.include_router(
#     container_routes.router, prefix="/containers", tags=["containers"])

router.include_router(
    code_routes.router, prefix="/code-elements", tags=["code-elements"]
)

router.include_router(logger_routes.router, prefix="/logs", tags=["logs"])

router.include_router(document_routes.router,
                      prefix="/documents", tags=["documents"])

router.include_router(test_routes.router, prefix="/tests", tags=["tests"])

router.include_router(
    play_ground_routes.router, prefix="/playgrounds", tags=["playgrounds"]
)

router.include_router(
    versioning_router, prefix="/versioning", tags=["versioning"])

router.include_router(container_routes.router,
                      prefix="/containers", tags=["containers"])

# router.include_router(call_routes.router, prefix="/calls", tags=["calls"])

router.include_router(group_routes.router, prefix="/groups", tags=["groups"])

router.include_router(
    conversation_routes.router,
    prefix="/conversations",
    tags=["conversations"],
)

router.include_router(
    walkthrough_routes.router,
    prefix="/walkthroughs",
    tags=["walkthroughs"],
)
