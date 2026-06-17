from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.config.constants import ScalingMethod

class ScalingRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    columns: List[str] = Field(..., description="List of numerical columns to scale.")
    method: ScalingMethod = Field(ScalingMethod.STANDARD, description="Scaling method: 'standard', 'minmax', 'robust'.")

class ScalingPreviewResponse(BaseModel):
    affected_rows: int = Field(..., description="Number of rows scaled.")
    sample_before: List[Dict[str, Any]] = Field(..., description="Sample of columns before scaling.")
    sample_after: List[Dict[str, Any]] = Field(..., description="Sample of columns after scaling.")
