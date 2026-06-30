import os
import json
import pytest

@pytest.fixture
def kb_data():
    kb_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "ml", "kb", "ml_algorithm_kb.json"
    )
    with open(kb_path, "r") as f:
        return json.load(f)

@pytest.fixture
def templates_data():
    templates_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "ml", "kb", "preprocessing_templates.json"
    )
    with open(templates_path, "r") as f:
        return json.load(f)

@pytest.fixture
def hyperparameters_data():
    hp_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app", "ml", "kb", "hyperparameters.json"
    )
    with open(hp_path, "r") as f:
        return json.load(f)

def test_kb_integrity(kb_data, templates_data, hyperparameters_data):
    # Total algorithms must be 37
    assert len(kb_data) == 37
    
    valid_speeds = {"fast", "medium", "slow"}
    valid_accuracies = {"low", "medium", "high", "very_high"}
    valid_interpretabilities = {"high", "medium", "low"}
    valid_families = {
        "linear", "tree_ensemble", "boosting", "distance_based",
        "kernel", "bayesian", "neural", "time_series", "survival"
    }
    
    for algo in kb_data:
        algo_id = algo.get("id")
        name = algo.get("name")
        
        # Check basic properties
        assert algo_id is not None, "Algorithm ID is missing"
        assert name is not None, f"Algorithm name is missing for ID {algo_id}"
        assert algo.get("category") is not None
        assert algo.get("description") is not None
        
        # Check constraints
        assert algo.get("speed") in valid_speeds, f"{algo_id} has invalid speed: {algo.get('speed')}"
        assert algo.get("accuracy_potential") in valid_accuracies, f"{algo_id} has invalid accuracy: {algo.get('accuracy_potential')}"
        assert algo.get("interpretability") in valid_interpretabilities, f"{algo_id} has invalid interpretability: {algo.get('interpretability')}"
        assert algo.get("family") in valid_families, f"{algo_id} has invalid family: {algo.get('family')}"
        
        # Check explainability mapping
        exp = algo.get("explainability")
        assert exp is not None, f"{algo_id} is missing explainability block"
        assert "shap_support" in exp
        assert "feature_importance" in exp
        assert "coefficients" in exp
        assert "supports_partial_dependence" in exp
        assert "supports_permutation_importance" in exp
        assert "supports_lime" in exp
        
        # Check that it exists in preprocessing templates
        assert algo_id in templates_data, f"{algo_id} is missing preprocessing template in preprocessing_templates.json"
        
        # Check that it exists in hyperparameters
        assert algo_id in hyperparameters_data, f"{algo_id} is missing hyperparameters template in hyperparameters.json"
