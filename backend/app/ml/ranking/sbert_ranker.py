"""
SBERT-based ranker that computes cosine similarity between dataset description
and algorithm descriptions. Caches algorithm embeddings to disk.
"""
import logging
import os
import pickle
import json
from typing import List, Tuple

import numpy as np

from app.ml.schemas.algorithm_schema import AlgorithmEntry

logger = logging.getLogger(__name__)

# Path to cached embeddings
_EMBEDDINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "embeddings")
_CACHE_PATH = os.path.join(_EMBEDDINGS_DIR, "cached_embeddings.pkl")

# Path to KB file
_KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kb", "ml_algorithm_kb.json")


def _get_kb_hash() -> str:
    """Get a simple hash of the KB file to detect changes."""
    try:
        stat = os.stat(_KB_PATH)
        return f"{stat.st_size}_{stat.st_mtime}"
    except OSError:
        return ""


def _load_cached_embeddings() -> dict:
    """Load cached embeddings from disk if they exist and are valid."""
    if not os.path.exists(_CACHE_PATH):
        logger.info("No cached embeddings found, will compute fresh.")
        return None

    try:
        with open(_CACHE_PATH, "rb") as f:
            cache = pickle.load(f)

        # Validate cache structure
        if not isinstance(cache, dict) or "kb_hash" not in cache or "embeddings" not in cache or "ids" not in cache:
            logger.warning("Invalid cache structure, will recompute.")
            return None

        # Check if KB has changed
        current_hash = _get_kb_hash()
        if cache["kb_hash"] != current_hash:
            logger.info("KB file has changed since embeddings were cached, will recompute.")
            return None

        logger.info(f"Loaded cached embeddings for {len(cache['ids'])} algorithms.")
        return cache
    except Exception as e:
        logger.warning(f"Failed to load cached embeddings: {e}")
        return None


def _save_cached_embeddings(ids: List[str], embeddings: np.ndarray, kb_hash: str) -> None:
    """Save embeddings to disk."""
    try:
        os.makedirs(_EMBEDDINGS_DIR, exist_ok=True)
        cache = {
            "kb_hash": kb_hash,
            "ids": ids,
            "embeddings": embeddings
        }
        with open(_CACHE_PATH, "wb") as f:
            pickle.dump(cache, f)
        logger.info(f"Saved cached embeddings for {len(ids)} algorithms to disk.")
    except Exception as e:
        logger.warning(f"Failed to save cached embeddings: {e}")


def _compute_embeddings(algorithms: List[AlgorithmEntry]) -> Tuple[List[str], np.ndarray]:
    """Compute SBERT embeddings for all algorithm descriptions."""
    from app.ml.models.sentence_model import encode

    ids = [algo.id for algo in algorithms]
    descriptions = [algo.description for algo in algorithms]

    logger.info(f"Computing SBERT embeddings for {len(descriptions)} algorithms...")
    embeddings = encode(descriptions)
    logger.info(f"Computed embeddings: shape={embeddings.shape}")

    return ids, embeddings


def _get_algorithm_embeddings(algorithms: List[AlgorithmEntry]) -> Tuple[List[str], np.ndarray]:
    """Get algorithm embeddings, using cache if available."""
    # Try loading from cache
    cache = _load_cached_embeddings()
    if cache is not None:
        return cache["ids"], cache["embeddings"]

    # Compute fresh
    ids, embeddings = _compute_embeddings(algorithms)

    # Save to cache
    kb_hash = _get_kb_hash()
    _save_cached_embeddings(ids, embeddings, kb_hash)

    return ids, embeddings


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def rank_algorithms(
    algorithms: List[AlgorithmEntry],
    feature_description: str,
    top_n: int = 8
) -> List[AlgorithmEntry]:
    """
    Rank algorithms by SBERT cosine similarity to the dataset feature description.
    Combines similarity score with filter_score for final ranking.

    Args:
        algorithms: List of algorithm entries (post-filter).
        feature_description: Natural language dataset description from profiler.
        top_n: Number of top results to return.

    Returns:
        Sorted list of top_n algorithms with updated similarity_score and combined_score.
    """
    if not algorithms:
        return []

    if not feature_description.strip():
        logger.warning("Empty feature description, ranking by filter_score only.")
        for algo in algorithms:
            algo.similarity_score = 0.5
            algo.combined_score = 0.5 + algo.filter_score
        algorithms.sort(key=lambda a: a.combined_score, reverse=True)
        return algorithms[:top_n]

    # Get algorithm embeddings
    ids, embeddings = _get_algorithm_embeddings(algorithms)

    # Build lookup from id -> embedding
    id_to_embedding = {}
    for i, algo_id in enumerate(ids):
        id_to_embedding[algo_id] = embeddings[i]

    # Encode the dataset description
    from app.ml.models.sentence_model import encode_single
    query_embedding = encode_single(feature_description)

    # Compute similarity for each candidate algorithm
    for algo in algorithms:
        if algo.id in id_to_embedding:
            algo.similarity_score = _cosine_similarity(query_embedding, id_to_embedding[algo.id])
        else:
            # Algorithm not in embedding cache (shouldn't happen, but handle gracefully)
            algo.similarity_score = 0.0

        # Combined score: 70% similarity + 30% filter adjustments (normalized)
        algo.combined_score = (0.7 * algo.similarity_score) + (0.3 * (0.5 + algo.filter_score))

    # Sort by combined score descending
    algorithms.sort(key=lambda a: a.combined_score, reverse=True)

    top = algorithms[:top_n]
    logger.info(
        f"SBERT ranking: top {len(top)} algorithms — "
        f"best={top[0].name} (sim={top[0].similarity_score:.3f}, combined={top[0].combined_score:.3f})"
    )

    return top
