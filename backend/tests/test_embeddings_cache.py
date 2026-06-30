import os
import tempfile
import pickle
import numpy as np
import pytest
from unittest.mock import patch
from app.ml.ranking import sbert_ranker

@pytest.fixture
def temp_cache_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_embeddings_cache_save_and_load(temp_cache_dir):
    cache_path = os.path.join(temp_cache_dir, "test_cache.pkl")
    kb_path = os.path.join(temp_cache_dir, "test_kb.json")
    
    # Create a dummy KB file
    with open(kb_path, "w") as f:
        f.write("[]")
        
    dummy_ids = ["algo1", "algo2"]
    dummy_embeddings = np.random.randn(2, 384)
    
    with patch("app.ml.ranking.sbert_ranker._CACHE_PATH", cache_path), \
         patch("app.ml.ranking.sbert_ranker._KB_PATH", kb_path):
         
        # Ensure no cache exists initially
        assert sbert_ranker._load_cached_embeddings() is None
        
        # Save cache
        kb_hash = sbert_ranker._get_kb_hash()
        sbert_ranker._save_cached_embeddings(dummy_ids, dummy_embeddings, kb_hash)
        
        # Load and verify
        loaded = sbert_ranker._load_cached_embeddings()
        assert loaded is not None
        assert loaded["ids"] == dummy_ids
        np.testing.assert_array_equal(loaded["embeddings"], dummy_embeddings)
        assert loaded["kb_hash"] == kb_hash

def test_embeddings_cache_invalidation_on_kb_change(temp_cache_dir):
    cache_path = os.path.join(temp_cache_dir, "test_cache.pkl")
    kb_path = os.path.join(temp_cache_dir, "test_kb.json")
    
    # 1. Create a dummy KB file
    with open(kb_path, "w") as f:
        f.write("[]")
        
    dummy_ids = ["algo1"]
    dummy_embeddings = np.random.randn(1, 384)
    
    with patch("app.ml.ranking.sbert_ranker._CACHE_PATH", cache_path), \
         patch("app.ml.ranking.sbert_ranker._KB_PATH", kb_path):
         
        # Save cache
        kb_hash = sbert_ranker._get_kb_hash()
        sbert_ranker._save_cached_embeddings(dummy_ids, dummy_embeddings, kb_hash)
        
        # Ensure it loads
        assert sbert_ranker._load_cached_embeddings() is not None
        
        # Modify the KB file (changes its size/mtime hash)
        with open(kb_path, "w") as f:
            f.write("[{}, {}]")
            
        # Verify cache is invalidated (loads as None)
        assert sbert_ranker._load_cached_embeddings() is None
