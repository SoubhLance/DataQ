from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.config.constants import OutlierMethod, OutlierAction

class OutlierColumnDetail(BaseModel):
    column: str = Field(..., description="Numerical column name.")
    outliers: int = Field(..., description="Number of detected outlier values.")
    percentage: float = Field(..., description="Percentage of outlier values in the column.")
    lower_bound: Optional[float] = Field(None, description="Lower threshold (IQR/Z-score only).")
    upper_bound: Optional[float] = Field(None, description="Upper threshold (IQR/Z-score only).")

class OutlierCheckResponse(BaseModel):
    method: OutlierMethod = Field(..., description="Method used for outlier detection.")
    columns: List[OutlierColumnDetail] = Field(..., description="Outlier details per numerical column.")

class OutlierRemoveRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    column: str = Field(..., description="Numerical column to treat.")
    method: OutlierMethod = Field(OutlierMethod.IQR, description="Method for outlier identification: 'iqr', 'zscore', 'iforest'.")
    action: OutlierAction = Field(OutlierAction.REMOVE, description="Action: 'remove' (drops rows), 'cap' (clips values to bounds), 'keep' (no-op).")
    threshold: float = Field(3.0, description="Z-score threshold (Z-score method only).")
    contamination: float = Field(0.05, description="Contamination ratio (Isolation Forest only).")

class OutlierPreviewResponse(BaseModel):
    affected_rows: int = Field(..., description="Number of rows modified or dropped.")
    sample_before: List[Dict[str, Any]] = Field(..., description="Sample of outliers before treatment.")
    sample_after: List[Dict[str, Any]] = Field(..., description="Sample of dataset after treatment (for the same rows).")
