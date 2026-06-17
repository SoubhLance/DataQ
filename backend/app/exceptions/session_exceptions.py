class SessionException(Exception):
    """Base exception for session-related errors."""
    pass

class SessionNotFound(SessionException):
    """Raised when a requested session UUID is not found in cache."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session with ID '{session_id}' not found.")

class SessionExpired(SessionException):
    """Raised when a session has expired and been removed."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        super().__init__(f"Session with ID '{session_id}' has expired.")
