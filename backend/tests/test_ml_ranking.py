import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.ml.schemas.algorithm_schema import AlgorithmEntry, ExplainabilityInfo
from app.ml.ranking.sbert_ranker import rank_algorithms, _cosine_similarity

@pytest.fixture
def mock_algorithms():
    return [
        AlgorithmEntry(
            id="rf_class",
            name="Random Forest Classifier",
            category="classification",
            description="Random forest model for classification.",
            strengths=[],
            weaknesses=[],
            min_samples=1,
            max_features=None,
            handles_categorical=False,
            handles_imbalance=False,
            interpretability="Medium",
            speed="Medium",
            accuracy_potential="High",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=False, partial_dependence=True),
            sklearn_class="sklearn.ensemble.RandomForestClassifier",
            filter_score=0.0
        ),
        AlgorithmEntry(
            id="logistic_reg",
            name="Logistic Regression",
            category="classification",
            description="Linear classification model.",
            strengths=[],
            weaknesses=[],
            min_samples=1,
            max_features=None,
            handles_categorical=False,
            handles_imbalance=False,
            interpretability="High",
            speed="Fast",
            accuracy_potential="Medium",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=True, partial_dependence=True),
            sklearn_class="sklearn.linear_model.LogisticRegression",
            filter_score=0.0
        )
    ]

def test_cosine_similarity():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    c = np.array([0.0, 1.0, 0.0])
    
    assert _cosine_similarity(a, b) == pytest.approx(1.0)
    assert _cosine_similarity(a, c) == pytest.approx(0.0)

@patch("app.ml.models.sentence_model.encode")
@patch("app.ml.models.sentence_model.encode_single")
def test_rank_algorithms(mock_encode_single, mock_encode, mock_algorithms):
    # Setup mock vectors (384 dimensional for MiniLM)
    # RF embedding is orthogonal to query; Logistic matches query
    mock_rf_vec = np.zeros(384)
    mock_rf_vec[0] = 1.0
    
    mock_lr_vec = np.zeros(384)
    mock_lr_vec[1] = 1.0
    
    # query matches Logistic
    mock_query_vec = np.zeros(384)
    mock_query_vec[1] = 1.0
    
    mock_encode.return_value = np.vstack([mock_rf_vec, mock_lr_vec])
    mock_encode_single.return_value = mock_query_vec
    
    ranked = rank_algorithms(mock_algorithms, "classification dataset", top_n=2)
    
    assert len(ranked) == 2
    # Logistic should be ranked first because similarity is 1.0 vs RF's 0.0
    assert ranked[0].id == "logistic_reg"
    assert ranked[0].similarity_score == pytest.approx(1.0)
    assert ranked[1].id == "rf_class"
    assert ranked[1].similarity_score == pytest.approx(0.0)
