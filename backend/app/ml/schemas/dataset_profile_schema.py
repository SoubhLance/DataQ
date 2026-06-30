"""
Pydantic schemas for ML dataset profiling.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class DatasetProfile(BaseModel):
    """ML-specific dataset profile extracted for recommendation engine."""
    session_id: str
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    numeric_count: int = Field(ge=0)
    categorical_count: int = Field(ge=0)
    datetime_count: int = Field(ge=0)
    binary_count: int = Field(ge=0)
    numeric_ratio: float = Field(ge=0.0, le=1.0)
    categorical_ratio: float = Field(ge=0.0, le=1.0)
    missing_ratio: float = Field(ge=0.0, le=1.0)
    outlier_ratio: float = Field(ge=0.0, le=1.0)
    dimensionality_ratio: float = Field(ge=0.0, description="columns / rows")
    target_column: Optional[str] = None
    problem_type: Optional[str] = Field(
        None,
        description="classification, regression, clustering, time_series, survival_analysis, dimensionality_reduction"
    )
    class_balance: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Ratio of minority to majority class. None for regression."
    )
    high_cardinality_columns: List[str] = Field(default_factory=list)
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    feature_description: str = Field(
        default="",
        description="Natural language summary for SBERT embedding"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc-123",
                "row_count": 891,
                "column_count": 12,
                "numeric_count": 7,
                "categorical_count": 5,
                "datetime_count": 0,
                "binary_count": 1,
                "numeric_ratio": 0.58,
                "categorical_ratio": 0.42,
                "missing_ratio": 0.12,
                "outlier_ratio": 0.03,
                "dimensionality_ratio": 0.013,
                "target_column": "Survived",
                "problem_type": "classification",
                "class_balance": 0.62,
                "high_cardinality_columns": ["Name", "Ticket"],
                "numeric_columns": ["Age", "Fare", "SibSp", "Parch"],
                "categorical_columns": ["Sex", "Embarked", "Pclass"],
                "feature_description": "Tabular dataset with 891 rows, 12 columns. Binary classification target 'Survived'. 58% numeric, 42% categorical. Low missing ratio. Low outlier ratio."
            }
        }
    )
