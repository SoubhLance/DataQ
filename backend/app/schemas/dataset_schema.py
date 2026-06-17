from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class UploadResponse(BaseModel):
    session_id: str = Field(..., description="UUID representing the session.")
    rows: int = Field(..., description="Number of rows in the dataset.")
    columns: int = Field(..., description="Number of columns in the dataset.")
    filename: str = Field(..., description="Uploaded filename.")

class ColumnInspect(BaseModel):
    name: str = Field(..., description="Column name.")
    dtype: str = Field(..., description="Data type representation.")
    missing: int = Field(..., description="Count of missing values.")
    missing_percent: float = Field(..., description="Percentage of missing values.")
    unique: int = Field(..., description="Count of unique values.")
    cardinality: float = Field(..., description="Unique ratio (unique / total_rows).")

class InspectResponse(BaseModel):
    shape: List[int] = Field(..., description="Dimensions: [rows, columns].")
    columns: List[ColumnInspect] = Field(..., description="Detailed stats per column.")
    numeric_columns: List[str] = Field(..., description="Names of numerical columns.")
    categorical_columns: List[str] = Field(..., description="Names of categorical columns.")
    memory_usage_mb: float = Field(..., description="Memory footprint in Megabytes.")

class QualityResponse(BaseModel):
    score: int = Field(..., description="Calculated dataset quality score out of 100.")
    warnings: List[str] = Field(..., description="Identified quality issues / warnings.")

class CorrelationResponse(BaseModel):
    matrix: Dict[str, Dict[str, Optional[float]]] = Field(..., description="Pearson correlation matrix.")
    highly_correlated: List[Dict[str, Any]] = Field(..., description="Pairs of columns with Pearson coefficient > 0.9 or < -0.9.")

class ImbalanceResponse(BaseModel):
    ratio: str = Field(..., description="Formatted class ratio representation (e.g., '90:10').")
    imbalanced: bool = Field(..., description="True if dataset class distribution is heavily skewed.")
    class_counts: Dict[str, int] = Field(..., description="Frequency count of target categories.")
