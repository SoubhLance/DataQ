from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    """
    Represents an asynchronous or long-running background task
    (e.g., uploading, isolation forest, scaling, AI chat, report generation).
    """
    task_id: str
    session_id: str
    type: str  # e.g., "upload", "outliers", "scaling", "report", "chat"
    status: TaskStatus = TaskStatus.QUEUED
    progress: int = 0
    message: str = "Task initialized."
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
