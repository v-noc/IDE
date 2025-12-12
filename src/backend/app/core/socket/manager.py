import socketio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SocketManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SocketManager, cls).__new__(cls)
            cls._instance.server = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*"
            )
            cls._instance.app = socketio.ASGIApp(cls._instance.server)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._setup_handlers()

    def _setup_handlers(self):
        @self.server.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")

        @self.server.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")

        @self.server.event
        async def join_project(sid, project_id: str):
            """Frontend joins a room specific to a project to get updates."""
            logger.info(f"Client {sid} joined project room: {project_id}")
            await self.server.enter_room(sid, project_id)

    async def emit_to_project(self, project_id: str, event: str, data: Any):
        """Emit an event to all users viewing a specific project."""
        try:
            await self.server.emit(event, data, room=project_id)
        except Exception as e:
            logger.error(f"Failed to emit socket event: {e}")


# Global accessor
get_socket_manager = SocketManager
