import time
import threading
import logging
from datetime import datetime
from typing import Optional
from app.config.settings import settings
from app.utils.dataframe_cache import cache_manager

logger = logging.getLogger(__name__)

class CacheCleanupThread(threading.Thread):
    """
    Background daemon thread that periodically checks for expired sessions
    and removes them from the CacheManager.
    """
    def __init__(self, interval_seconds: int = 60):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.daemon = True
        self._stop_event = threading.Event()

    def run(self):
        logger.info("Session Cache Cleanup Thread Started.")
        while not self._stop_event.is_set():
            try:
                # Sleep in increments checking for stop events to allow fast shutdown
                for _ in range(self.interval_seconds):
                    if self._stop_event.is_set():
                        return
                    time.sleep(1)
                
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cache cleanup thread: {str(e)}")

    def stop(self):
        self._stop_event.set()

    def cleanup_expired_sessions(self):
        """Scan cache manager for expired sessions and delete them."""
        session_keys = cache_manager.list_keys()
        now = datetime.now()
        timeout = settings.SESSION_TIMEOUT
        
        for session_id in session_keys:
            state = cache_manager.get(session_id)
            if state:
                elapsed = (now - state.last_accessed).total_seconds()
                if elapsed > timeout:
                    logger.info(f"Session '{session_id}' expired. Inactive for {elapsed:.1f}s. Evicting from cache.")
                    cache_manager.delete(session_id)


# Global thread control
_cleanup_thread: Optional[CacheCleanupThread] = None

def start_cache_cleanup_service(interval_seconds: int = 60) -> None:
    """Start the background cache cleanup daemon thread."""
    global _cleanup_thread
    if _cleanup_thread is None or not _cleanup_thread.is_alive():
        _cleanup_thread = CacheCleanupThread(interval_seconds)
        _cleanup_thread.start()

def stop_cache_cleanup_service() -> None:
    """Stop the background cache cleanup daemon thread."""
    global _cleanup_thread
    if _cleanup_thread is not None:
        _cleanup_thread.stop()
        _cleanup_thread.join(timeout=5)
        _cleanup_thread = None
