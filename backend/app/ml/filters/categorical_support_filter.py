"""
Categorical support filter: adjusts scores based on how well algorithms
handle datasets with many categorical features.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)

# If categorical ratio > this, apply categorical-heavy adjustments
CATEGORICAL_HEAVY_THRESHOLD = 0.4

# Algorithms that struggle with many one-hot encoded features
_CATEGORICAL_SENSITIVE = {
    "svm_classifier", "svr", "knn_classifier",
    "mlp_classifier", "logistic_regression",
    "linear_regression", "ridge_regression", "lasso_regression", "elasticnet_regression"
}

# Algorithms with native categorical support — boost these
_CATEGORICAL_NATIVE = {
    "catboost_classifier", "catboost_regressor",
    "lightgbm_classifier", "lightgbm_regressor",
    "naive_bayes"
}

# Tree-based algorithms that handle label-encoded categoricals well
_TREE_BASED = {
    "decision_tree_classifier", "decision_tree_regressor",
    "random_forest_classifier", "random_forest_regressor",
    "extra_trees_classifier",
    "xgboost_classifier", "xgboost_regressor",
    "gradient_boosting_classifier", "gradient_boosting_regressor",
    "adaboost_classifier"
}

CATEGORICAL_NATIVE_BOOST = 0.15
CATEGORICAL_TREE_BOOST = 0.08
CATEGORICAL_SENSITIVE_PENALTY = -0.10

# Additional penalty for high cardinality + SVM/KNN
HIGH_CARDINALITY_PENALTY = -0.05


def filter_by_categorical_support(
    algorithms: List[AlgorithmEntry],
    profile: DatasetProfile
) -> List[AlgorithmEntry]:
    """
    Adjust filter_score based on the dataset's categorical feature composition.

    - Native categorical handlers (CatBoost, LightGBM): boosted
    - Tree-based (RF, XGBoost, etc): moderately boosted
    - One-hot-heavy sensitive (SVM, KNN, MLP): penalized
    - Extra penalty if high cardinality columns exist

    Args:
        algorithms: List of algorithm entries.
        profile: Dataset profile.

    Returns:
        Same list with adjusted filter_score values.
    """
    cat_ratio = profile.categorical_ratio
    has_high_cardinality = len(profile.high_cardinality_columns) > 0

    if cat_ratio <= CATEGORICAL_HEAVY_THRESHOLD and not has_high_cardinality:
        logger.debug(f"Categorical filter: low categorical ratio ({cat_ratio}), skipping")
        return algorithms

    logger.info(
        f"Categorical filter: heavy categorical data "
        f"(ratio={cat_ratio}, high_cardinality={has_high_cardinality})"
    )

    for algo in algorithms:
        if algo.id in _CATEGORICAL_NATIVE:
            algo.filter_score += CATEGORICAL_NATIVE_BOOST
            logger.debug(f"  Boosted {algo.name} (+{CATEGORICAL_NATIVE_BOOST}) [native categorical]")
        elif algo.id in _TREE_BASED:
            algo.filter_score += CATEGORICAL_TREE_BOOST
            logger.debug(f"  Boosted {algo.name} (+{CATEGORICAL_TREE_BOOST}) [tree-based]")
        elif algo.id in _CATEGORICAL_SENSITIVE:
            algo.filter_score += CATEGORICAL_SENSITIVE_PENALTY
            logger.debug(f"  Penalized {algo.name} ({CATEGORICAL_SENSITIVE_PENALTY}) [one-hot sensitive]")

            # Extra penalty for high cardinality
            if has_high_cardinality:
                algo.filter_score += HIGH_CARDINALITY_PENALTY
                logger.debug(f"  Extra penalty {algo.name} ({HIGH_CARDINALITY_PENALTY}) [high cardinality]")

    return algorithms
