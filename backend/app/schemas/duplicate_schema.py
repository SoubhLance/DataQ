from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class KeepOption(str, Enum):
    FIRST = "first"
    LAST = "last"
    NONE = "none" # Represents dropping all duplicates (keep=False in Pandas)

class DuplicateDetectResponse(BaseModel):
    total_rows: int = Field(..., description="Total rows in the dataset.")
    duplicate_rows: int = Field(..., description="Count of duplicate rows.")
    duplicate_percent: float = Field(..., description="Percentage of rows that are duplicates.")

class DuplicateRemoveRequest(BaseModel):
    session_id: str = Field(..., description="Active session UUID.")
    keep: KeepOption = Field(KeepOption.FIRST, description="Strategy to keep duplicates: 'first', 'last', or 'none' (drop all).")

class DuplicatePreviewResponse(BaseModel):
    affected_rows: int = Field(..., description="Number of duplicate rows that will be deleted.")
    sample_before: List[Dict[str, Any]] = Field(..., description="Sample of duplicate rows.")
    sample_after: List[Dict[str, Any]] = Field(..., description="Sample of dataset after removing duplicates.")
