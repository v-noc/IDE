from fastapi import FastAPI
from contextlib import asynccontextmanager
from .api import root, health
from .db.client import get_db


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the application's lifespan.
    Handles startup and shutdown events.
    """
    # Startup
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
    lifespan=lifespan
)

# Include routers
app.include_router(root.router)
app.include_router(health.router, tags=["health"])
# app.include_router(users.router, prefix="/users", tags=["users"])
# app.include_router(projects.router, prefix="/projects", tags=["projects"])


