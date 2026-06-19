import os
from typing import List, Any
import pandas as pd
from app.config.settings import settings
from app.exceptions.validation_exceptions import UnsupportedFileType, FileTooLarge, ValidationException
from app.exceptions.dataset_exceptions import ColumnNotFound, InvalidDtype

def validate_uploaded_file(filename: str, file_size: int) -> None:
    """
    Validate size and extension of uploaded file.
    """
    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(filename, settings.ALLOWED_EXTENSIONS)
        
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise FileTooLarge(file_size, settings.MAX_UPLOAD_SIZE)

def validate_columns_exist(df: pd.DataFrame, columns: List[str]) -> None:
    """
    Verify that all specified columns exist in the DataFrame.
    """
    for col in columns:
        if col not in df.columns:
            raise ColumnNotFound(col)

def validate_column_dtype_compatibility(df: pd.DataFrame, col: str, target_dtype: str) -> None:
    """
    Check if a column can be realistically cast to the target data type.
    """
    if col not in df.columns:
        raise ColumnNotFound(col)
        
    series = df[col].dropna()
    if series.empty:
        return # Empty column can always be cast

    target = target_dtype.lower()
    
    if target == "int":
        try:
            # Check if values are numeric/convertible
            pd.to_numeric(series, errors='raise')
        except (ValueError, TypeError) as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be converted to integer: {str(e)}")
            
    elif target == "float":
        try:
            pd.to_numeric(series, errors='raise')
        except (ValueError, TypeError) as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be converted to float: {str(e)}")
            
    elif target == "datetime":
        try:
            pd.to_datetime(series, errors='raise', format='mixed')
        except (ValueError, TypeError, OverflowError) as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be parsed as date/time: {str(e)}")
            
    elif target == "string":
        # String is always compatible
        pass
        
    else:
        raise InvalidDtype(col, target_dtype, "Unsupported target data type.")

def validate_file_content(filepath: str, filename: str, content_type: str) -> None:
    """
    Harden file upload validation using MIME checks and magic-byte checks.
    """
    import os
    
    _, ext = os.path.splitext(filename.lower())
    
    try:
        with open(filepath, "rb") as f:
            header = f.read(8)
    except Exception as e:
        raise ValidationException(f"Failed to read file for validation: {str(e)}")
        
    if ext == '.parquet':
        if not header.startswith(b'PAR1'):
            raise ValidationException("File content does not match Parquet format (missing 'PAR1' signature).")
        if content_type and content_type not in ["application/octet-stream", "application/x-parquet", "application/parquet"]:
            raise ValidationException(f"Invalid Content-Type for Parquet file: {content_type}")
            
    elif ext == '.xlsx':
        if not header.startswith(b'PK\x03\x04'):
            raise ValidationException("File content does not match Excel (.xlsx) format (missing ZIP archive signature).")
        if content_type and content_type not in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/zip",
            "application/octet-stream"
        ]:
            raise ValidationException(f"Invalid Content-Type for Excel file: {content_type}")
            
    elif ext == '.json':
        stripped = header.strip()
        if not (stripped.startswith(b'{') or stripped.startswith(b'[')):
            raise ValidationException("File content does not match JSON format (missing '{' or '[' start character).")
        if content_type and content_type not in ["application/json", "text/plain"]:
            raise ValidationException(f"Invalid Content-Type for JSON file: {content_type}")
            
    elif ext == '.csv':
        if b'\x00' in header:
            raise ValidationException("File content contains binary null bytes, indicating it is not a valid text CSV.")
        if header.startswith(b'PK\x03\x04') or header.startswith(b'PAR1'):
            raise ValidationException("File content has a binary zip/parquet signature, but file extension is .csv.")
        if content_type and content_type not in [
            "text/csv", "text/plain", "application/vnd.ms-excel", "text/x-csv", "application/csv", "application/x-csv"
        ]:
            raise ValidationException(f"Invalid Content-Type for CSV file: {content_type}")
    else:
        raise UnsupportedFileType(filename, settings.ALLOWED_EXTENSIONS)

def safe_resolve_path(base_dir: str, relative_path: str):
    """
    Resolve and sanitize the path, ensuring it remains within the base directory.
    Prevents path traversal attacks.
    """
    from pathlib import Path
    base = Path(base_dir).resolve()
    target = Path(base_dir).joinpath(relative_path).resolve()
    
    if not target.is_relative_to(base):
        raise ValidationException("Path traversal detected: Access denied outside storage directories.")
    return target

def sanitize_session_id(session_id: str) -> str:
    """
    Validate that session_id is a valid UUID string to prevent any path traversal or injection.
    """
    import uuid
    try:
        val = uuid.UUID(session_id)
        return str(val)
    except ValueError:
        raise ValidationException("Invalid session ID format. Must be a valid UUID.")
