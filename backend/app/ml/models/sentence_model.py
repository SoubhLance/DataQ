"""
Singleton SBERT model loader using sentence-transformers.
Loads all-MiniLM-L6-v2 lazily on first call.
"""
import logging
import threading
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_MODEL_NAME = "all-MiniLM-L6-v2"


def _load_model():
    """Load the sentence-transformers model. Called once."""
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        # Double-check after acquiring lock
        if _model is not None:
            return _model

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SBERT model '{_MODEL_NAME}'...")
            _model = SentenceTransformer(_MODEL_NAME)
            logger.info(f"SBERT model '{_MODEL_NAME}' loaded successfully.")
            return _model
        except Exception as e:
            logger.error(f"Failed to load SBERT model '{_MODEL_NAME}': {e}")
            raise RuntimeError(f"Failed to load SBERT model: {e}") from e


def encode(texts: List[str]) -> np.ndarray:
    """
    Encode a list of text strings into dense embeddings.

    Args:
        texts: List of strings to encode.

    Returns:
        numpy array of shape (len(texts), embedding_dim).
    """
    model = _load_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings


def encode_single(text: str) -> np.ndarray:
    """
    Encode a single text string into a dense embedding.

    Args:
        text: String to encode.

    Returns:
        numpy array of shape (embedding_dim,).
    """
    model = _load_model()
    embedding = model.encode([text], convert_to_numpy=True, show_progress_bar=False)
    return embedding[0]


def is_loaded() -> bool:
    """Check if the model is currently loaded in memory."""
    return _model is not None
