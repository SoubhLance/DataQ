"""
Pydantic schemas for ML recommendation request/response.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.ml.schemas.dataset_profile_schema import DatasetProfile


class RecommendRequest(BaseModel):
    """Request body for POST /api/v1/ml/recommend."""
    session_id: str
    target_column: Optional[str] = None
    problem_type: Optional[str] = Field(
        None,
        description="classification, regression, clustering, time_series, survival_analysis, dimensionality_reduction. Auto-detected if not provided."
    )
    goal: Optional[str] = Field(
        None,
        description="Natural language goal, e.g. 'heart disease classification'"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc-123",
                "target_column": "Survived",
                "goal": "predict passenger survival on Titanic"
            }
        }
    )


class AlgorithmRecommendation(BaseModel):
    """Single algorithm recommendation with role and reasoning."""
    id: str
    name: str
    category: str
    role: str = Field(
        description="recommended, fastest, best_accuracy_boost, most_interpretable"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Derived from cosine similarity + filter adjustments")
    similarity_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    explainability: Dict[str, bool] = Field(default_factory=dict)


class AlternativeComparison(BaseModel):
    """Comparison table row for alternative algorithms."""
    algorithm: str
    role: str
    speed: str
    accuracy: str
    interpretability: str
    handles_categorical: bool = False
    handles_imbalance: bool = False
    confidence: float = Field(ge=0.0, le=1.0)


class SuggestedPipelineStep(BaseModel):
    """Single step in the suggested preprocessing pipeline."""
    step: str
    component: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class RecommendResponse(BaseModel):
    """Full response from POST /api/v1/ml/recommend."""
    session_id: str
    problem_type: str
    dataset_profile: DatasetProfile
    recommendations: AlgorithmRecommendation = Field(
        description="Primary recommended algorithm"
    )
    alternatives: List[AlternativeComparison] = Field(
        default_factory=list,
        description="Comparison table of top alternatives"
    )
    suggested_pipeline: List[SuggestedPipelineStep] = Field(
        default_factory=list,
        description="Ordered preprocessing steps"
    )
    pipeline_code: str = Field(
        default="",
        description="Generated sklearn Pipeline code"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence of the primary recommendation (legacy, same as pipeline_confidence)"
    )
    pipeline_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence of the recommended ML pipeline"
    )
    preprocessing_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence of the suggested preprocessing pipeline"
    )
    all_recommendations: List[AlgorithmRecommendation] = Field(
        default_factory=list,
        description="All ranked algorithm recommendations"
    )


class FeedbackRequest(BaseModel):
    """Request body for user feedback on model recommendations."""
    session_id: str
    recommended_algorithm: str
    accepted: bool
    user_id: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc-123",
                "recommended_algorithm": "random_forest_classifier",
                "accepted": True
            }
        }
    )
