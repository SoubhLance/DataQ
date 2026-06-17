from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.config.constants import EncodingMethod, DataType

class ColumnDropRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    columns: List[str] = Field(..., description="List of columns to drop.")

class ColumnRenameRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    old_name: str = Field(..., description="Old column name.")
    new_name: str = Field(..., description="New column name.")

class ColumnCastRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    column: str = Field(..., description="Column name to cast.")
    new_dtype: DataType = Field(..., description="Target data type: 'int', 'float', 'string', 'datetime'.")

class ColumnEncodeRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    column: str = Field(..., description="Column name to encode.")
    method: EncodingMethod = Field(EncodingMethod.LABEL, description="Encoding method: 'label' (LabelEncoder) or 'onehot' (pd.get_dummies).")

class ColumnEncodePreviewResponse(BaseModel):
    affected_rows: int = Field(..., description="Number of rows encoded.")
    sample_before: List[Dict[str, Any]] = Field(..., description="Sample of column before encoding.")
    sample_after: List[Dict[str, Any]] = Field(..., description="Sample of dataset after encoding.")
