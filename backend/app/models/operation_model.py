from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any

class Operation(BaseModel):
    """
    Represents a single preprocessing step performed on the dataset.
    This model is used to replay operations for undo functionality,
    generate the final code pipeline, and serve audit log views.
    """
    type: str = Field(..., description="The type of operation (e.g., duplicates, missing, outliers, scaling, encode, column)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the operation")
    generated_code: str = Field(..., description="Equivalent pandas/scikit-learn Python code snippet")
    description: str = Field(..., description="Human-readable description of the operation for the audit log")
    created_at: datetime = Field(default_factory=datetime.now, description="Timestamp indicating when this operation was applied")
