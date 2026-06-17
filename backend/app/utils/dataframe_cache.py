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
        
    def peek(self, session_id: str) -> Optional[SessionState]:
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

    def peek(self, session_id: str) -> Optional[SessionState]:
        with self._lock:
            return self._cache.get(session_id)

    def set(self, session_id: str, state: SessionState) -> None:
        with self._lock:
            state.touch()
            self._cache[session_id] = state

    def delete(self, session_id: str) -> None:
        state = None
        with self._lock:
            if session_id in self._cache:
                state = self._cache[session_id]
                del self._cache[session_id]
        if state:
            from app.utils.file_utils import cleanup_session_files
            cleanup_session_files(state)

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
    from app.utils.validators import sanitize_session_id
    session_id = sanitize_session_id(session_id)
    state = cache_manager.get(session_id)
    if not state:
        raise SessionNotFound(session_id)
    return state
