from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .api import root, health
from .api.core.projects import crud as projects_crud
from .api.core.files import virtual_files
from .api.core.folder import virtual_folders
from .db.client import get_db
from .utils.logging import setup_logging
from .utils.exceptions import generic_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the application's lifespan.
    Handles startup and shutdown events.
    """
    # Startup
    setup_logging()
    db = get_db()
    try:
        db.properties()
        print("✅ Database connection established successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🔄 Shutting down database connections...")


app = FastAPI(
    title="V-NOC API",
    version="1.0.0",
    description="API for the V-NOC project",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add exception handlers
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(root.router)
app.include_router(health.router, tags=["health"])
app.include_router(projects_crud.router, prefix="/v1/api", tags=["projects"])
app.include_router(
    virtual_files.router, prefix="/v1/api", tags=["virtual_files"]
)
app.include_router(
    virtual_folders.router, prefix="/v1/api", tags=["virtual_folders"]
)