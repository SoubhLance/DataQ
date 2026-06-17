import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from app.services.task_service import task_service
from app.utils.websocket_manager import ws_manager
from app.models.task_model import Task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Tasks & WebSockets"])

@router.get("/tasks/{task_id}", response_model=Task)
async def get_task_status(task_id: str):
    """
    Get the current execution status, progress, and results of a background task.
    """
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )
    return task

@router.websocket("/ws/session/{session_id}")
async def websocket_session_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket channel for real-time progress update broadcasts for a given session.
    """
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Wait for any text (keep-alive / messages) from the client
            data = await websocket.receive_text()
            # Log ping or messages if needed
            logger.debug(f"Received WebSocket message from session {session_id}: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket disconnected gracefully for session {session_id}")
    except Exception as e:
        ws_manager.disconnect(session_id, websocket)
        logger.error(f"WebSocket error in session {session_id}: {str(e)}")
