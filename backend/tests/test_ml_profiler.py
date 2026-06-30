import pandas as pd
import numpy as np
import pytest
from app.ml.profiling.dataset_profiler import profile_dataset, clear_cache, _profile_cache

def test_profile_dataset_classification():
    # Setup classification dataframe
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "feature2": np.random.choice(["A", "B", "C"], size=100),
        "target": np.random.choice([0, 1], size=100)
    })
    
    profile = profile_dataset(df, session_id="test_session_class", target_column="target")
    
    assert profile.row_count == 100
    assert profile.column_count == 3
    assert profile.problem_type == "classification"
    assert profile.target_column == "target"
    assert profile.class_balance is not None
    assert "target" in profile.feature_description
    assert "Classification" in profile.feature_description

def test_profile_dataset_regression():
    # Setup regression dataframe
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "target": np.random.randn(100) * 10
    })
    
    profile = profile_dataset(df, session_id="test_session_regr", target_column="target")
    
    assert profile.problem_type == "regression"
    assert profile.target_column == "target"
    assert "Regression" in profile.feature_description

def test_profile_dataset_clustering_default():
    # Setup clustering dataframe (no target)
    df = pd.DataFrame({
        "feature1": np.random.randn(100),
        "feature2": np.random.randn(100)
    })
    
    profile = profile_dataset(df, session_id="test_session_cluster")
    
    assert profile.problem_type == "clustering"
    assert profile.target_column is None
    assert "Clustering" in profile.feature_description

def test_profile_dataset_caching():
    df = pd.DataFrame({
        "feature1": np.random.randn(10),
        "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    })
    
    clear_cache()
    assert len(_profile_cache) == 0
    
    # Profile and cache
    profile1 = profile_dataset(df, session_id="cache_session", target_column="target")
    assert "cache_session" in _profile_cache
    
    # Re-profile should hit cache
    profile2 = profile_dataset(df, session_id="cache_session", target_column="target")
    assert profile1 is profile2  # same object
    
    # Changing target should recompute
    profile3 = profile_dataset(df, session_id="cache_session", target_column="feature1")
    assert profile3 is not profile1
    
    # Clear cache
    clear_cache("cache_session")
    assert "cache_session" not in _profile_cache
