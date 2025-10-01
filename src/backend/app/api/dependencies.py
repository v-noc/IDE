from fastapi import Depends
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.db.client import get_db
from arango.database import StandardDatabase
from app.core.services.container_service import ContainerService


def get_project_service(db: StandardDatabase = Depends(get_db)) -> ProjectService:
    repos = Repositories(db)
    return ProjectService(repos)


def get_container_service(db: StandardDatabase = Depends(get_db)) -> ContainerService:
    repos = Repositories(db)
    return ContainerService(repos)
