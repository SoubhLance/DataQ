import pytest
import os
from app.utils.validators import safe_resolve_path
from app.exceptions.validation_exceptions import ValidationException

@pytest.mark.unit
def test_path_security_traversal_blocked():
    """Verify that safe_resolve_path blocks directory traversal attempts."""
    base_dir = os.path.abspath(".")
    
    # Try traversing up to Windows directories or general parent folders
    traversal_path = "../../../windows/system32"
    
    with pytest.raises(ValidationException) as excinfo:
        safe_resolve_path(base_dir, traversal_path)
        
    assert "Path traversal detected" in str(excinfo.value)

@pytest.mark.unit
def test_path_security_valid_path():
    """Verify that a valid relative path within the base directory resolves successfully."""
    base_dir = os.path.abspath(".")
    valid_relative = "tests/conftest.py"
    
    resolved = safe_resolve_path(base_dir, valid_relative)
    assert resolved.exists()
    assert resolved.is_file()
