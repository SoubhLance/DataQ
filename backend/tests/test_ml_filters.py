import pytest
from app.ml.schemas.algorithm_schema import AlgorithmEntry, ExplainabilityInfo
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.filters.problem_type_filter import filter_by_problem_type
from app.ml.filters.dataset_size_filter import filter_by_dataset_size
from app.ml.filters.imbalance_filter import filter_by_imbalance
from app.ml.filters.dimensionality_filter import filter_by_dimensionality
from app.ml.filters.categorical_support_filter import filter_by_categorical_support

@pytest.fixture
def base_algorithms():
    return [
        AlgorithmEntry(
            id="logistic_regression",
            name="Logistic Regression",
            category="classification",
            description="Linear model for classification.",
            strengths=[],
            weaknesses=[],
            min_samples=10,
            max_features=None,
            handles_categorical=False,
            handles_imbalance=True,
            interpretability="High",
            speed="Fast",
            accuracy_potential="Medium",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=True, partial_dependence=True),
            sklearn_class="sklearn.linear_model.LogisticRegression",
            filter_score=0.0
        ),
        AlgorithmEntry(
            id="linear_regression",
            name="Linear Regression",
            category="regression",
            description="Linear model for regression.",
            strengths=[],
            weaknesses=[],
            min_samples=5,
            max_features=100,
            handles_categorical=False,
            handles_imbalance=False,
            interpretability="High",
            speed="Fast",
            accuracy_potential="Low",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=True, partial_dependence=True),
            sklearn_class="sklearn.linear_model.LinearRegression",
            filter_score=0.0
        ),
        AlgorithmEntry(
            id="catboost_classifier",
            name="CatBoost Classifier",
            category="classification",
            description="Gradient boosting on decision trees with native categorical support.",
            strengths=[],
            weaknesses=[],
            min_samples=20,
            max_features=None,
            handles_categorical=True,
            handles_imbalance=True,
            interpretability="Low",
            speed="Medium",
            accuracy_potential="High",
            explainability=ExplainabilityInfo(shap_support=True, feature_importance=True, coefficients=False, partial_dependence=True),
            sklearn_class="catboost.CatBoostClassifier",
            filter_score=0.0
        ),
    ]

@pytest.fixture
def mock_profile():
    return DatasetProfile(
        session_id="test_filter_session",
        row_count=15,
        column_count=10,
        numeric_count=5,
        categorical_count=5,
        datetime_count=0,
        binary_count=0,
        numeric_ratio=0.5,
        categorical_ratio=0.5,
        missing_ratio=0.0,
        outlier_ratio=0.0,
        dimensionality_ratio=0.666667, # cols / rows = 10 / 15
        target_column="target",
        problem_type="classification",
        class_balance=0.1,  # highly imbalanced
        high_cardinality_columns=[],
        numeric_columns=["col1", "col2", "col3", "col4", "col5"],
        categorical_columns=["col6", "col7", "col8", "col9", "col10"],
        feature_description="test"
    )

def test_problem_type_filter(base_algorithms, mock_profile):
    filtered = filter_by_problem_type(base_algorithms, mock_profile)
    assert len(filtered) == 2
    categories = [algo.category for algo in filtered]
    assert "classification" in categories
    assert "regression" not in categories

def test_dataset_size_filter(base_algorithms, mock_profile):
    # row_count is 15. Logistic (needs 10), Linear (needs 5), CatBoost (needs 20)
    filtered = filter_by_dataset_size(base_algorithms, mock_profile)
    assert len(filtered) == 2
    ids = [algo.id for algo in filtered]
    assert "logistic_regression" in ids
    assert "linear_regression" in ids
    assert "catboost_classifier" not in ids

def test_imbalance_filter(base_algorithms, mock_profile):
    # mock_profile is classification and class_balance=0.1 (imbalanced)
    # handles_imbalance: Logistic (True), Linear (False), CatBoost (True)
    res = filter_by_imbalance(base_algorithms, mock_profile)
    
    logistic = next(a for a in res if a.id == "logistic_regression")
    linear = next(a for a in res if a.id == "linear_regression")
    
    assert logistic.filter_score == 0.15
    assert linear.filter_score == -0.10

def test_dimensionality_filter(base_algorithms, mock_profile):
    # dimensionality_ratio is 0.666667 (> 0.5)
    res = filter_by_dimensionality(base_algorithms, mock_profile)
    
    logistic = next(a for a in res if a.id == "logistic_regression")
    assert logistic.filter_score > -0.01 # should not be penalized or might be boosted/penalized depending on model type
    
def test_categorical_support_filter(base_algorithms, mock_profile):
    # categorical_ratio is 0.5 (many categorical columns)
    res = filter_by_categorical_support(base_algorithms, mock_profile)
    
    catboost = next(a for a in res if a.id == "catboost_classifier")
    logistic = next(a for a in res if a.id == "logistic_regression")
    
    # CatBoost native categorical support should be boosted
    assert catboost.filter_score > logistic.filter_score
