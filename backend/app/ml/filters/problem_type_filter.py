"""
Problem type filter: keeps only algorithms matching the detected problem type.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)

# Map problem types to their matching algorithm categories
_CATEGORY_MAP = {
    "classification": ["classification"],
    "regression": ["regression"],
    "clustering": ["clustering"],
    "dimensionality_reduction": ["dimensionality_reduction"],
    "time_series": ["time_series"],
    "survival_analysis": ["survival_analysis"],
}


def filter_by_problem_type(
    algorithms: List[AlgorithmEntry],
    profile: DatasetProfile
) -> List[AlgorithmEntry]:
    """
    Filter algorithms to only those matching the dataset's problem type.

    Args:
        algorithms: Full list of algorithm entries from KB.
        profile: Dataset profile with detected problem type.

    Returns:
        Filtered list of algorithms.
    """
    problem_type = profile.problem_type
    if not problem_type:
        logger.warning("No problem type detected, returning all algorithms.")
        return algorithms

    allowed_categories = _CATEGORY_MAP.get(problem_type, [])
    if not allowed_categories:
        logger.warning(f"Unknown problem type '{problem_type}', returning all algorithms.")
        return algorithms

    filtered = [algo for algo in algorithms if algo.category in allowed_categories]
    logger.info(
        f"Problem type filter: {len(algorithms)} -> {len(filtered)} "
        f"(type={problem_type})"
    )
    return filtered
