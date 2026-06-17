import os
import uuid
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query
from app.schemas.dataset_schema import UploadResponse
from app.services.file_service import FileService
from app.services.task_service import task_service
from app.config.settings import settings
from app.utils.file_utils import load_file_to_dataframe
from app.models.session_model import SessionState
from app.utils.dataframe_cache import cache_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])

def run_background_upload(temp_filepath: str, filename: str, content_type: str, session_id: str, task_id: str):
    """Background task to load dataframe and cache session state."""
    try:
        task_service.update_task_progress(task_id, 20, "Analyzing file format...")
        
        # Validate magic bytes and MIME content
        from app.utils.validators import validate_file_content
        validate_file_content(temp_filepath, filename, content_type)
        
        # Load DataFrame from file
        task_service.update_task_progress(task_id, 50, "Parsing dataset rows...")
        df = load_file_to_dataframe(temp_filepath, filename)
        
        task_service.update_task_progress(task_id, 80, "Initializing session state...")
        session_state = SessionState(
            session_id=session_id,
            filename=filename,
            df=df
        )
        session_state.uploaded_filepath = temp_filepath
        cache_manager.set(session_id, session_state)
        
        # Task completed
        result = {
            "session_id": session_id,
            "rows": session_state.rows,
            "columns": session_state.columns,
            "filename": filename
        }
        task_service.complete_task(task_id, result=result)
    except Exception as e:
        logger.exception(f"Background upload failed for session {session_id}")
        task_service.fail_task(task_id, str(e))
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

@router.post("")
async def upload_dataset(
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Whether to run upload asynchronously in the background."),
    file: UploadFile = File(...)
):
    """
    Upload a dataset file (CSV, XLSX, JSON, Parquet).
    Can be run synchronously or asynchronously with task updates.
    """
    if not background:
        # Synchronous mode
        session_state = await FileService.upload_dataset(file)
        return {
            "session_id": session_state.session_id,
            "rows": session_state.rows,
            "columns": session_state.columns,
            "filename": session_state.filename
        }
    else:
        # Background Async Mode
        session_id = str(uuid.uuid4())
        task = task_service.create_task(session_id, "upload")
        
        # Save uploaded file temporarily
        _, ext = os.path.splitext(file.filename.lower())
        temp_filename = f"{session_id}{ext}"
        temp_filepath = os.path.join(settings.UPLOADS_DIR, temp_filename)
        
        # Save upload to file
        task_service.update_task_progress(task.task_id, 10, "Receiving file stream...")
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        background_tasks.add_task(run_background_upload, temp_filepath, file.filename, file.content_type, session_id, task.task_id)
        
        return {
            "task_id": task.task_id,
            "session_id": session_id,
            "message": "File upload started in background."
        }

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Manually delete session and its associated files from cache and disk.
    """
    from app.utils.validators import sanitize_session_id
    from app.exceptions.session_exceptions import SessionNotFound
    
    session_id = sanitize_session_id(session_id)
    
    if cache_manager.peek(session_id) is None:
        raise SessionNotFound(session_id)
        
    cache_manager.delete(session_id)
    return {
        "success": True,
        "message": f"Session '{session_id}' and all associated files deleted successfully."
    }
