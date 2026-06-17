from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.config.constants import MissingStrategy

class MissingColumnDetail(BaseModel):
    column: str = Field(..., description="Column name.")
    missing: int = Field(..., description="Count of missing/null values.")
    percent: float = Field(..., description="Percentage of missing values in the column.")
    recommended: str = Field(..., description="Recommended strategy: 'mean', 'median', 'mode', 'drop', or 'none'.")

class MissingCheckResponse(BaseModel):
    columns: List[MissingColumnDetail] = Field(..., description="List of columns and their missing value statistics.")

class MissingApplyRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    column: str = Field(..., description="Column name to apply imputation.")
    strategy: MissingStrategy = Field(..., description="Imputation strategy.")
    constant_value: Optional[Any] = Field(None, description="Constant value if strategy is 'constant'.")

class MissingPreviewResponse(BaseModel):
    affected_rows: int = Field(..., description="Number of rows imputed or dropped.")
    sample_before: List[Dict[str, Any]] = Field(..., description="Rows containing null values before change.")
    sample_after: List[Dict[str, Any]] = Field(..., description="Same rows after applying imputation strategy.")
