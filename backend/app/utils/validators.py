import os
from typing import List, Any
import pandas as pd
from app.config.settings import settings
from app.exceptions.validation_exceptions import UnsupportedFileType, FileTooLarge
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
        except Exception as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be converted to integer: {str(e)}")
            
    elif target == "float":
        try:
            pd.to_numeric(series, errors='raise')
        except Exception as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be converted to float: {str(e)}")
            
    elif target == "datetime":
        try:
            pd.to_datetime(series, errors='raise')
        except Exception as e:
            raise InvalidDtype(col, target_dtype, f"Values cannot be parsed as date/time: {str(e)}")
            
    elif target == "string":
        # String is always compatible
        pass
        
    else:
        raise InvalidDtype(col, target_dtype, "Unsupported target data type.")
