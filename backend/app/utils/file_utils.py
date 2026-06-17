import os
import pandas as pd
from typing import Union
from app.exceptions.validation_exceptions import UnsupportedFileType
from app.exceptions.dataset_exceptions import EmptyDataset, OperationError

def load_file_to_dataframe(file_path: str, original_filename: str) -> pd.DataFrame:
    """
    Load an uploaded dataset file into a Pandas DataFrame.
    Supports CSV, XLSX, JSON, Parquet.
    """
    _, ext = os.path.splitext(original_filename.lower())
    
    try:
        if ext == '.csv':
            # Handle potential delimiter variations (defaulting to comma)
            df = pd.read_csv(file_path)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, engine='openpyxl')
        elif ext == '.json':
            df = pd.read_json(file_path)
        elif ext == '.parquet':
            df = pd.read_parquet(file_path, engine='pyarrow')
        else:
            raise UnsupportedFileType(original_filename, ['.csv', '.xlsx', '.json', '.parquet'])
    except UnsupportedFileType:
        raise
    except (FileNotFoundError, ValueError, TypeError, UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as e:
        raise OperationError("File Loading", f"Failed to parse file: {str(e)}")

    if df.empty:
        raise EmptyDataset()
        
    return df

def save_dataframe_to_file(df: pd.DataFrame, file_path: str, format_ext: str) -> str:
    """
    Saves a DataFrame to the local filesystem in a specified format.
    Returns the absolute path to the saved file.
    """
    ext = format_ext.lower()
    if not ext.startswith('.'):
        ext = f".{ext}"
        
    try:
        if ext == '.csv':
            df.to_csv(file_path, index=False)
        elif ext in ['.xlsx', '.xls']:
            df.to_excel(file_path, index=False, engine='openpyxl')
        elif ext == '.json':
            # Write JSON in a records format for readability
            df.to_json(file_path, orient='records', indent=2)
        elif ext == '.parquet':
            df.to_parquet(file_path, index=False, engine='pyarrow')
        else:
            raise OperationError("File Export", f"Unsupported export format '{format_ext}'")
    except Exception as e:
        raise OperationError("File Export", f"Failed to write file to disk: {str(e)}")
        
    return file_path

def cleanup_session_files(session) -> None:
    """
    Safely delete the uploaded, cleaned, and report files tracked by the session.
    """
    import os
    import logging
    from pathlib import Path
    from app.config.settings import settings

    logger = logging.getLogger(__name__)

    def safe_delete(filepath: str, base_dir: str, file_type: str) -> None:
        if not filepath:
            return
        try:
            target = Path(filepath).resolve()
            base = Path(base_dir).resolve()
            if not target.is_relative_to(base):
                logger.warning(f"Prevented deletion of file outside {base_dir}: {filepath}")
                return
            if target.exists():
                os.remove(target)
                logger.info(f"Deleted {file_type} file: {target}")
        except Exception as e:
            logger.error(f"Failed to delete {file_type} file {filepath}: {str(e)}")

    # 1. Uploaded file
    if session.uploaded_filepath:
        safe_delete(session.uploaded_filepath, settings.UPLOADS_DIR, "uploaded")

    # 2. Cleaned files
    for filepath in session.cleaned_filepaths:
        safe_delete(filepath, settings.CLEANED_DIR, "cleaned")

    # 3. Report files
    for filepath in session.report_filepaths:
        safe_delete(filepath, settings.REPORTS_DIR, "report")
