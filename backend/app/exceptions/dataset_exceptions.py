class DatasetException(Exception):
    """Base exception for dataset-related manipulation errors."""
    pass

class ColumnNotFound(DatasetException):
    """Raised when a specified column name is not found in the dataframe."""
    def __init__(self, column: str):
        self.column = column
        super().__init__(f"Column '{column}' not found in dataset.")

class InvalidDtype(DatasetException):
    """Raised when a cast to an invalid or incompatible dtype is requested."""
    def __init__(self, column: str, dtype: str, details: str = ""):
        self.column = column
        self.dtype = dtype
        self.details = details
        msg = f"Cannot cast column '{column}' to '{dtype}'."
        if details:
            msg += f" Details: {details}"
        super().__init__(msg)

class EmptyDataset(DatasetException):
    """Raised when the dataset has zero rows or is empty."""
    def __init__(self):
        super().__init__("The dataset is empty (contains no rows).")

class OperationError(DatasetException):
    """Raised when a pandas/scikit-learn operation fails during processing."""
    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Error executing operation '{operation}': {details}")
