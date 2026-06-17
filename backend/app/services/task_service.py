import uuid
import asyncio
import logging
import threading
from datetime import datetime
from typing import Dict, Optional, Any, List
from app.models.task_model import Task, TaskStatus
from app.utils.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

class TaskService:
    """
    Thread-safe service managing background task states, progress reports,
    and WebSocket live updates.
    """
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    def create_task(self, session_id: str, task_type: str) -> Task:
        """Create a new background task and register it."""
        with self._lock:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                session_id=session_id,
                type=task_type,
                status=TaskStatus.QUEUED,
                progress=0,
                message="Task queued."
            )
            self._tasks[task_id] = task
            logger.info(f"Task created: {task_id} (Type: {task_type}, Session: {session_id})")
            
            self._notify_progress(task)
            return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve task details by ID."""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task_progress(self, task_id: str, progress: int, message: str) -> None:
        """Update the progress (0-100) and status message of a task, triggering ws updates."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.warning(f"Attempted to update progress on non-existent task: {task_id}")
                return
                
            task.progress = min(max(progress, 0), 100)
            task.message = message
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.now()
            
            logger.debug(f"Task {task_id} progress: {progress}% - {message}")
            self._notify_progress(task)

    def complete_task(self, task_id: str, result: Any = None) -> None:
        """Mark task as successfully completed."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
                
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.message = "Task completed successfully."
            task.result = result
            task.updated_at = datetime.now()
            
            logger.info(f"Task completed: {task_id}")
            self._notify_progress(task)

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
                
            task.status = TaskStatus.FAILED
            task.error = error
            task.message = f"Task failed: {error}"
            task.updated_at = datetime.now()
            
            logger.error(f"Task failed: {task_id} - {error}")
            self._notify_progress(task)

    def _notify_progress(self, task: Task) -> None:
        """Broadcast progress updates to session WS connections."""
        payload = {
            "type": "progress",
            "task_id": task.task_id,
            "task_type": task.type,
            "status": task.status.value,
            "progress": task.progress,
            "message": task.message,
            "error": task.error,
            "result": task.result
        }
        
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast_to_session(task.session_id, payload))
        except RuntimeError:
            # Fallback if no active event loop is running (e.g. testing)
            pass

# Singleton Task Service
task_service = TaskService()
