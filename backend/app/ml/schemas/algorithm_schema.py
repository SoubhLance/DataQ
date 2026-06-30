"""
Pydantic schemas for ML algorithm KB entries.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ExplainabilityInfo(BaseModel):
    """Explainability capabilities of an algorithm."""
    shap_support: bool = False
    feature_importance: bool = False
    coefficients: bool = False
    partial_dependence: bool = False  # Keep for backward compatibility
    supports_partial_dependence: bool = False
    supports_permutation_importance: bool = False
    supports_lime: bool = False


class AlgorithmEntry(BaseModel):
    """Single algorithm from the knowledge base."""
    id: str
    name: str
    category: str = Field(
        description="classification, regression, clustering, dimensionality_reduction, time_series, survival_analysis"
    )
    family: str = Field(
        default="linear",
        description="linear, tree_ensemble, boosting, distance_based, kernel, bayesian, neural, time_series, survival"
    )
    description: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    min_samples: int = 0
    max_features: Optional[int] = None
    handles_imbalance: bool = False
    handles_categorical: bool = False
    interpretability: str = Field(
        default="medium",
        description="high, medium, low"
    )
    speed: str = Field(
        default="medium",
        description="fast, medium, slow"
    )
    accuracy_potential: str = Field(
        default="medium",
        description="medium, high, very_high"
    )
    sklearn_class: str = ""
    explainability: ExplainabilityInfo = Field(default_factory=ExplainabilityInfo)

    # Mutable fields set during filtering/ranking
    filter_score: float = Field(default=0.0, description="Score from hard filters (boosted/penalized)")
    similarity_score: float = Field(default=0.0, description="SBERT cosine similarity score")
    combined_score: float = Field(default=0.0, description="Final combined score")


class AlgorithmRelationship(BaseModel):
    """Relationship mapping for a single algorithm."""
    upgrade: Optional[str] = None
    fast_alternative: Optional[str] = None
    interpretable_alternative: Optional[str] = None
    ensemble_partner: Optional[str] = None


class PreprocessingTemplate(BaseModel):
    """Required preprocessing steps for an algorithm."""
    scaling: Optional[str] = Field(None, description="standard, minmax, or null")
    encoding: Optional[str] = Field(None, description="onehot, label, or null")
    imputer: Optional[str] = Field(None, description="median, mean, ffill, or null")
    feature_selection: Optional[str] = Field(None, description="pca or null")
