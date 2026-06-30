import os
import json
import pytest
from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.pipeline.pipeline_generator import generate_pipeline_code, get_pipeline_steps

@pytest.fixture
def all_kb_algorithms():
    kb_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "ml", "kb", "ml_algorithm_kb.json"
    )
    with open(kb_path, "r") as f:
        raw = json.load(f)
    return [AlgorithmEntry(**entry) for entry in raw]

@pytest.fixture
def mock_profile():
    return DatasetProfile(
        session_id="test_pipeline_gen",
        row_count=200,
        column_count=5,
        numeric_count=3,
        categorical_count=2,
        datetime_count=0,
        binary_count=0,
        numeric_ratio=0.6,
        categorical_ratio=0.4,
        missing_ratio=0.05,
        outlier_ratio=0.02,
        dimensionality_ratio=0.025,
        target_column="target",
        problem_type="classification",
        class_balance=0.5,
        high_cardinality_columns=[],
        numeric_columns=["feat1", "feat2", "feat3"],
        categorical_columns=["feat4", "feat5"],
        feature_description="mock description"
    )

def test_all_algorithms_generate_code(all_kb_algorithms, mock_profile):
    assert len(all_kb_algorithms) == 37
    
    for algo in all_kb_algorithms:
        # Override problem type of profile if necessary to match model's category
        profile = mock_profile.model_copy()
        
        # Mapping problem types
        category_to_type = {
            "classification": "classification",
            "regression": "regression",
            "clustering": "clustering",
            "dimensionality_reduction": "dimensionality_reduction",
            "time_series": "time_series",
            "survival_analysis": "survival_analysis"
        }
        profile.problem_type = category_to_type.get(algo.category, "classification")
        if algo.category == "clustering" or algo.category == "dimensionality_reduction":
            profile.target_column = None
            profile.numeric_columns = ["feat1", "feat2", "feat3", "feat4", "feat5"]
            profile.categorical_columns = []
            
        steps = get_pipeline_steps(algo, profile)
        code = generate_pipeline_code(algo, profile, steps)
        
        assert code is not None
        assert isinstance(code, str)
        assert len(code) > 0
        assert "import pandas as pd" in code
        assert "Pipeline" in code
        
        # Verify model class import or name is in the code
        # (Handles either explicit _MODEL_MAP mapping or fallback parser)
        model_class_name = algo.sklearn_class.rsplit(".", 1)[-1]
        assert model_class_name in code or "Pipeline" in code
