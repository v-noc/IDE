import socketio
import logging
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SocketIOMount:
    """ASGI wrapper to properly mount socket.io at /ws path."""

    def __init__(self, socket_app):
        self.socket_app = socket_app

    async def __call__(self, scope, receive, send):
        # FastAPI's mount doesn't strip the mount path for WebSocket connections
        # So /ws/socket.io/ stays as /ws/socket.io/, but socket.io expects /socket.io/
        # We need to strip the /ws prefix manually
        original_path = scope.get("path", "")
        scope_type = scope.get("type", "unknown")

        # Strip /ws prefix if present (for both HTTP and WebSocket)
        if original_path.startswith("/ws"):
            path = original_path[3:]  # Remove "/ws"
            # Ensure path starts with / (socket.io expects /socket.io/)
            if not path.startswith("/"):
                path = "/" + path
        else:
            path = original_path

        # Only handle requests that are for socket.io
        if not path.startswith("/socket.io"):
            logger.warning(
                f"Socket.io mount received non-socket.io path: {original_path} -> {path} (type: {scope_type})")
            # Return 404 for non-socket.io paths
            if scope_type == "http":
                await send({
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [[b"content-type", b"text/plain"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Not Found",
                })
            elif scope_type == "websocket":
                await send({"type": "websocket.close"})
            return

        # Update the scope path to what socket.io expects
        scope["path"] = path
        if "raw_path" in scope:
            scope["raw_path"] = path.encode()

        # Debug logging for socket.io connections
        logger.debug(
            f"Socket.io request: {scope_type} {original_path} -> {path}")

        # Call socket.io app - wrap in error handling to catch WebSocket/HTTP protocol mismatches
        try:
            await self.socket_app(scope, receive, send)
        except RuntimeError as e:
            # Catch the specific error where socket.io tries to send HTTP response for WebSocket
            error_msg = str(e)
            if "Expected ASGI message" in error_msg and scope_type == "websocket":
                logger.error(
                    f"Socket.io protocol mismatch for WebSocket at {path}: {error_msg}. "
                    "This usually means socket.io didn't recognize the route."
                )
                # Close the WebSocket connection gracefully
                try:
                    await send({"type": "websocket.close"})
                except Exception:
                    pass  # Connection might already be closed
            else:
                # Re-raise other RuntimeErrors
                raise
        except Exception as e:
            logger.error(
                f"Unexpected error in socket.io mount: {e} (path: {path}, type: {scope_type})")
            raise


class SocketManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SocketManager, cls).__new__(cls)
            cls._instance.server = socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*"
            )
            # Create ASGI app - socket.io handles /socket.io/ path automatically
            socket_app = socketio.ASGIApp(cls._instance.server)
            # Wrap it to handle mounting at /ws
            cls._instance.app = SocketIOMount(socket_app)
            logger.info("🔌 Socket.IO server initialized")

        return cls._instance

    def __init__(self):
        # Prevent re-initialization
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._setup_handlers()

    def _setup_handlers(self):
        @self.server.event
        async def connect(sid, environ):
            """Handle client connection."""
            client_ip = environ.get("REMOTE_ADDR", "unknown")
            user_agent = environ.get("HTTP_USER_AGENT", "unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"✅ [{timestamp}] Client connected - "
                f"SID: {sid[:8]}..., IP: {client_ip}, "
                f"User-Agent: {user_agent[:50]}"
            )

        @self.server.event
        async def disconnect(sid):
            """Handle client disconnection."""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"❌ [{timestamp}] Client disconnected - "
                f"SID: {sid[:8]}..."
            )

        @self.server.event
        async def join_project(sid, project_id: str):
            """Frontend joins a room specific to a project to get updates."""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(
                f"📦 [{timestamp}] Client {sid[:8]}... joined project room: {project_id}"
            )
            await self.server.enter_room(sid, project_id)

    async def emit_to_project(self, project_id: str, event: str, data: Any):
        """Emit an event to all users viewing a specific project."""
        try:
            await self.server.emit(event, data, room=project_id)
        except Exception as e:
            logger.error(f"Failed to emit socket event: {e}")


# Global accessor
get_socket_manager = SocketManager
