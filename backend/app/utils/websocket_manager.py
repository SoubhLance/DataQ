import logging
from fastapi import WebSocket
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages active WebSocket connections mapped by session ID.
    Used for streaming progress and task update notifications.
    """
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session: {session_id}. Active count: {len(self.active_connections[session_id])}")

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")

    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]) -> None:
        """Broadcast JSON payload to all connected sockets in a session."""
        if session_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send websocket message in session {session_id}: {str(e)}")
                    dead_connections.append(connection)
            
            # Clean up dead sockets
            for connection in dead_connections:
                self.disconnect(session_id, connection)

# Singleton Connection Manager
ws_manager = ConnectionManager()
