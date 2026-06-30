"""
Dataset size filter: removes algorithms requiring more samples than available.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)


def filter_by_dataset_size(
    algorithms: List[AlgorithmEntry],
    profile: DatasetProfile
) -> List[AlgorithmEntry]:
    """
    Filter out algorithms that require more samples than the dataset provides.
    Also filters by max_features if the dataset has more features than supported.

    Args:
        algorithms: List of algorithm entries from KB (post problem-type filter).
        profile: Dataset profile with row_count and column_count.

    Returns:
        Filtered list of algorithms.
    """
    row_count = profile.row_count
    col_count = profile.column_count
    filtered = []

    for algo in algorithms:
        # Check minimum samples
        if algo.min_samples > row_count:
            logger.debug(
                f"Size filter: Removing {algo.name} "
                f"(needs {algo.min_samples} samples, have {row_count})"
            )
            continue

        # Check maximum features
        if algo.max_features is not None and col_count > algo.max_features:
            logger.debug(
                f"Size filter: Removing {algo.name} "
                f"(max {algo.max_features} features, have {col_count})"
            )
            continue

        filtered.append(algo)

    logger.info(
        f"Dataset size filter: {len(algorithms)} -> {len(filtered)} "
        f"(rows={row_count}, cols={col_count})"
    )
    return filtered
