from fastapi import APIRouter

from . import commits
from . import branchs

router = APIRouter()
router.include_router(commits.router, prefix="/commits", tags=["versioning"])
router.include_router(branchs.router, prefix="/branches", tags=["versioning"])
