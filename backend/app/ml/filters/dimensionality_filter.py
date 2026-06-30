"""
Dimensionality filter: penalizes algorithms that struggle with high feature-to-sample ratios.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)

# If cols/rows > this, consider high-dimensional
HIGH_DIM_THRESHOLD = 0.5

# Algorithms known to struggle with high dimensionality
_HIGH_DIM_SENSITIVE = {
    "knn_classifier", "svm_classifier", "svr", "dbscan",
    "hierarchical_clustering", "tsne"
}

# Algorithms that excel with high-dimensional data
_HIGH_DIM_FRIENDLY = {
    "lasso_regression", "elasticnet_regression", "pca", "umap",
    "random_forest_classifier", "random_forest_regressor",
    "xgboost_classifier", "xgboost_regressor",
    "lightgbm_classifier", "lightgbm_regressor"
}

HIGH_DIM_PENALTY = -0.12
HIGH_DIM_BOOST = 0.10


def filter_by_dimensionality(
    algorithms: List[AlgorithmEntry],
    profile: DatasetProfile
) -> List[AlgorithmEntry]:
    """
    Adjust filter_score based on dimensionality ratio (columns / rows).
    Penalizes algorithms that struggle with high-dimensional data.
    Boosts algorithms that handle it well.

    Args:
        algorithms: List of algorithm entries.
        profile: Dataset profile with dimensionality_ratio.

    Returns:
        Same list with adjusted filter_score values.
    """
    dim_ratio = profile.dimensionality_ratio

    if dim_ratio <= HIGH_DIM_THRESHOLD:
        logger.debug(f"Dimensionality filter: normal ratio ({dim_ratio})")
        return algorithms

    logger.info(f"Dimensionality filter: high-dimensional data (ratio={dim_ratio})")

    for algo in algorithms:
        if algo.id in _HIGH_DIM_SENSITIVE:
            algo.filter_score += HIGH_DIM_PENALTY
            logger.debug(f"  Penalized {algo.name} ({HIGH_DIM_PENALTY})")
        elif algo.id in _HIGH_DIM_FRIENDLY:
            algo.filter_score += HIGH_DIM_BOOST
            logger.debug(f"  Boosted {algo.name} (+{HIGH_DIM_BOOST})")

    return algorithms
