import pytest
from unittest.mock import patch, MagicMock
from app.ml.schemas.algorithm_schema import AlgorithmEntry, ExplainabilityInfo
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.reasoning.llm_reasoner import reason_with_llm, _rule_based_assignment

@pytest.fixture
def mock_profile():
    return DatasetProfile(
        session_id="test_reasoning",
        row_count=100,
        column_count=5,
        numeric_count=5,
        categorical_count=0,
        datetime_count=0,
        binary_count=0,
        numeric_ratio=1.0,
        categorical_ratio=0.0,
        missing_ratio=0.0,
        outlier_ratio=0.0,
        dimensionality_ratio=0.05,
        target_column="target",
        problem_type="classification",
        class_balance=0.5,
        high_cardinality_columns=[],
        numeric_columns=["col1", "col2", "col3", "col4", "col5"],
        categorical_columns=[],
        feature_description="test"
    )

@pytest.fixture
def mock_algorithms():
    return [
        AlgorithmEntry(
            id="rf_class",
            name="Random Forest Classifier",
            category="classification",
            description="Random forest model for classification.",
            min_samples=1,
            max_features=None,
            handles_categorical=False,
            handles_imbalance=False,
            interpretability="Medium",
            speed="Medium",
            accuracy_potential="High",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=False),
            sklearn_class="sklearn.ensemble.RandomForestClassifier",
            filter_score=0.0,
            combined_score=0.9
        ),
        AlgorithmEntry(
            id="logistic_reg",
            name="Logistic Regression",
            category="classification",
            description="Linear classification model.",
            min_samples=1,
            max_features=None,
            handles_categorical=False,
            handles_imbalance=False,
            interpretability="High",
            speed="Fast",
            accuracy_potential="Medium",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=True),
            sklearn_class="sklearn.linear_model.LogisticRegression",
            filter_score=0.0,
            combined_score=0.8
        )
    ]

def test_rule_based_fallback(mock_algorithms):
    # Rule-based fallback should assign roles based on metadata
    assignments = _rule_based_assignment(mock_algorithms)
    assert len(assignments) > 0
    roles = {a["role"] for a in assignments}
    assert "recommended" in roles
    assert "fastest" in roles
    
    # Logistic Regression has speed="Fast", should be fastest
    fastest = next(a for a in assignments if a["role"] == "fastest")
    assert fastest["id"] == "logistic_reg"

@patch("app.services.ai_service.ai_service.providers")
def test_reason_with_llm_sequential_fallback(mock_providers, mock_profile, mock_algorithms):
    # Mock providers: Groq fails, Gemini fails, Mistral succeeds
    groq = MagicMock()
    groq.generate.side_effect = Exception("Groq error")
    
    gemini = MagicMock()
    gemini.generate.side_effect = Exception("Gemini error")
    
    mistral = MagicMock()
    mistral.generate.return_value = '{"assignments": [{"id": "logistic_reg", "role": "recommended", "reasoning": "Mistral success"}]}'
    
    mock_providers.__iter__.return_value = [groq, gemini, mistral]
    
    assignments = reason_with_llm(mock_profile, mock_algorithms)
    
    # Assertions
    assert len(assignments) == 1
    assert assignments[0]["id"] == "logistic_reg"
    assert assignments[0]["role"] == "recommended"
    assert assignments[0]["reasoning"] == "Mistral success"
    
    groq.generate.assert_called_once()
    gemini.generate.assert_called_once()
    mistral.generate.assert_called_once()

@patch("app.services.ai_service.ai_service.providers")
def test_reason_with_llm_all_fail_fallback_rules(mock_providers, mock_profile, mock_algorithms):
    # All providers fail -> falls back to rule-based
    groq = MagicMock()
    groq.generate.side_effect = Exception("Groq error")
    gemini = MagicMock()
    gemini.generate.side_effect = Exception("Gemini error")
    mistral = MagicMock()
    mistral.generate.side_effect = Exception("Mistral error")
    
    mock_providers.__iter__.return_value = [groq, gemini, mistral]
    
    assignments = reason_with_llm(mock_profile, mock_algorithms)
    
    # Should get rule-based assignments
    assert len(assignments) > 0
    roles = {a["role"] for a in assignments}
    assert "recommended" in roles
    assert "fastest" in roles
