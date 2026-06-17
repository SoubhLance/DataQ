class ValidationException(Exception):
    """Base exception for user input/request validation errors."""
    pass

class UnsupportedFileType(ValidationException):
    """Raised when the uploaded file type is not supported."""
    def __init__(self, filename: str, allowed: list):
        self.filename = filename
        self.allowed = allowed
        super().__init__(f"Unsupported file type for file '{filename}'. Allowed: {allowed}")

class FileTooLarge(ValidationException):
    """Raised when the uploaded file exceeds size limits."""
    def __init__(self, size: int, limit: int):
        self.size = size
        self.limit = limit
        super().__init__(f"File size {size} bytes exceeds the limit of {limit} bytes.")

class InvalidRequestPayload(ValidationException):
    """Raised when the request payload contains validation issues."""
    pass
