from fastapi import FastAPI
from .api import users, root, health
from .db.client import get_db
from .db.dependencies import get_user_collection

app = FastAPI(
    title="V-NOC API",
    version="1.0.0",
    description="API for the V-NOC project",
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    # Test the database connection
    db = get_db()
    try:
        # Verify connection by getting database info
        db.properties()
        print("✅ Database connection established successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    print("🔄 Shutting down database connections...")

# Include routers
app.include_router(root.router)
app.include_router(health.router, tags=["health"])
app.include_router(users.router, prefix="/users", tags=["users"])

# Add dependency injection for database collections
app.dependency_overrides[get_user_collection] = get_user_collection
