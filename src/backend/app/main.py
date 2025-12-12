from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.socket.manager import get_socket_manager

from .api import root
from .db.client import get_db
from .core.watcher.service import WatcherService
from .utils.logging import setup_logging
from .utils.exceptions import generic_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the application's lifespan.
    Handles startup and shutdown events.
    """
    # Startup
    # setup_logging()
    db = get_db()
    try:
        db.properties()
        print("✅ Database connection established successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise

    # Initialize a process-wide watcher service singleton
    watcher_service = WatcherService()
    watcher_service.set_db(db)
    app.state.watcher_service = watcher_service

    # Init Socket Manager (creates the server instance)
    _ = get_socket_manager()
    print("🔌 Socket.IO server initialized and ready")

    yield

    # Shutdown
    print("🔄 Shutting down database connections...")
    # Stop file watchers gracefully
    try:
        service = getattr(app.state, "watcher_service", None)
        if service:
            service.stop_all()
    except Exception as e:
        print(f"⚠️ Failed to stop watchers cleanly: {e}")


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

# MOUNT SOCKET.IO
# This handles the /socket.io/ path automatically
socket_manager = get_socket_manager()
app.mount("/ws", socket_manager.app)
# Include the main router
app.include_router(root.router, prefix="/api/v1")
