"""
Imbalance filter: boosts algorithms that handle class imbalance when data is imbalanced.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)

# Threshold: if minority/majority ratio < this, consider imbalanced
IMBALANCE_THRESHOLD = 0.3

# Score boost for algorithms that handle imbalance
IMBALANCE_BOOST = 0.15

# Score penalty for algorithms that don't handle imbalance on imbalanced data
IMBALANCE_PENALTY = -0.10


def filter_by_imbalance(
    algorithms: List[AlgorithmEntry],
    profile: DatasetProfile
) -> List[AlgorithmEntry]:
    """
    Adjust filter_score for algorithms based on class imbalance.
    Does NOT remove algorithms — only boosts/penalizes scores.

    Args:
        algorithms: List of algorithm entries.
        profile: Dataset profile with class_balance info.

    Returns:
        Same list with adjusted filter_score values.
    """
    class_balance = profile.class_balance

    # Only applies to classification with known balance
    if profile.problem_type != "classification" or class_balance is None:
        logger.debug("Imbalance filter: skipped (not classification or no balance info)")
        return algorithms

    is_imbalanced = class_balance < IMBALANCE_THRESHOLD

    if not is_imbalanced:
        logger.debug(f"Imbalance filter: balanced dataset (ratio={class_balance})")
        return algorithms

    logger.info(f"Imbalance filter: imbalanced dataset detected (ratio={class_balance})")

    for algo in algorithms:
        if algo.handles_imbalance:
            algo.filter_score += IMBALANCE_BOOST
            logger.debug(f"  Boosted {algo.name} (+{IMBALANCE_BOOST})")
        else:
            algo.filter_score += IMBALANCE_PENALTY
            logger.debug(f"  Penalized {algo.name} ({IMBALANCE_PENALTY})")

    return algorithms
