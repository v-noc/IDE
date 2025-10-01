from fastapi import Depends
from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.db.client import get_db
from arango.database import StandardDatabase


def get_project_service(db: StandardDatabase = Depends(get_db)) -> ProjectService:
    repos = Repositories(db)
    return ProjectService(repos)
