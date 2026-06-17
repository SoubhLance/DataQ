import threading
from typing import Dict, Optional, List
from app.models.session_model import SessionState
from app.exceptions.session_exceptions import SessionNotFound

class CacheManager:
    """
    Interface for storage layer implementations (In-Memory, Redis, etc.)
    """
    def get(self, session_id: str) -> Optional[SessionState]:
        raise NotImplementedError
        
    def set(self, session_id: str, state: SessionState) -> None:
        raise NotImplementedError
        
    def delete(self, session_id: str) -> None:
        raise NotImplementedError

    def list_keys(self) -> List[str]:
        raise NotImplementedError


class MemoryCacheManager(CacheManager):
    """
    Thread-safe, in-memory implementation of CacheManager.
    """
    def __init__(self):
        self._cache: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[SessionState]:
        with self._lock:
            state = self._cache.get(session_id)
            if state:
                state.touch() # Update last accessed time
            return state

    def set(self, session_id: str, state: SessionState) -> None:
        with self._lock:
            state.touch()
            self._cache[session_id] = state

    def delete(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._cache:
                del self._cache[session_id]

    def list_keys(self) -> List[str]:
        with self._lock:
            return list(self._cache.keys())


# Singleton Instance
cache_manager = MemoryCacheManager()


def get_session(session_id: str) -> SessionState:
    """
    FastAPI dependency injection helper to retrieve session state from cache.
    Raises SessionNotFound if session ID is invalid or expired.
    """
    state = cache_manager.get(session_id)
    if not state:
        raise SessionNotFound(session_id)
    return state
