import os
import uuid
import shutil
import pandas as pd
from fastapi import UploadFile
from app.config.settings import settings
from app.models.session_model import SessionState
from app.utils.dataframe_cache import cache_manager
from app.utils.file_utils import load_file_to_dataframe
from app.utils.validators import validate_uploaded_file
from app.exceptions.validation_exceptions import ValidationException

class FileService:
    """
    Service responsible for handling file uploads, validation, and session initialization.
    """
    @staticmethod
    async def upload_dataset(file: UploadFile) -> SessionState:
        """
        Validate, save, and load the dataset. Initialize SessionState in cache.
        """
        # Determine temporary filepath
        session_id = str(uuid.uuid4())
        _, ext = os.path.splitext(file.filename.lower())
        temp_filename = f"{session_id}{ext}"
        temp_filepath = os.path.join(settings.UPLOADS_DIR, temp_filename)

        try:
            # We must read chunk by chunk to check size dynamically and avoid fully loading to memory first
            total_size = 0
            with open(temp_filepath, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                    total_size += len(chunk)
                    if total_size > settings.MAX_UPLOAD_SIZE:
                        raise ValidationException(f"File size exceeds the limit of {settings.MAX_UPLOAD_SIZE} bytes.")
                    buffer.write(chunk)
                    
            # Validate extension and size
            validate_uploaded_file(file.filename, total_size)
            
            # Harden upload validation: MIME and magic bytes
            from app.utils.validators import validate_file_content
            validate_file_content(temp_filepath, file.filename, file.content_type)
            
            # Load DataFrame from file
            df = load_file_to_dataframe(temp_filepath, file.filename)
            
            # Initialize Session State
            session_state = SessionState(
                session_id=session_id,
                filename=file.filename,
                df=df
            )
            session_state.uploaded_filepath = temp_filepath
            
            # Cache the Session State
            cache_manager.set(session_id, session_state)
            return session_state
            
        except Exception as e:
            # Cleanup temporary file if something went wrong
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise e
