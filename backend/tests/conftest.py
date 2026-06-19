import os
import shutil
import tempfile
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

# Pre-import and override settings before app starts if possible
from app.config.settings import settings

# Override directories with temp directory for testing
test_temp_dir = tempfile.mkdtemp(prefix="dataq_test_")
settings.STORAGE_DIR = os.path.join(test_temp_dir, "storage")
settings.UPLOADS_DIR = os.path.join(test_temp_dir, "storage", "uploads")
settings.CLEANED_DIR = os.path.join(test_temp_dir, "storage", "cleaned")
settings.REPORTS_DIR = os.path.join(test_temp_dir, "storage", "reports")

# Re-ensure directory creation
for directory in [settings.STORAGE_DIR, settings.UPLOADS_DIR, settings.CLEANED_DIR, settings.REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Now import the app
from app.main import app
from app.utils.dataframe_cache import cache_manager

@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """Cleanup session temporary folder after all tests finish."""
    yield
    if os.path.exists(test_temp_dir):
        shutil.rmtree(test_temp_dir)

@pytest.fixture(autouse=True)
def clean_cache_and_files():
    """Ensure each test starts with a clean cache and empty upload/cleaned/reports folders."""
    # Clear cache
    with cache_manager._lock:
        cache_manager._cache.clear()
    
    # Empty dirs
    for folder in [settings.UPLOADS_DIR, settings.CLEANED_DIR, settings.REPORTS_DIR]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
    yield

@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)

@pytest.fixture
def sample_dataframe():
    """
    Generate a standard sample dataframe for tests.
    Columns:
    - id (int)
    - name (string)
    - age (float, has NaN)
    - salary (float, has outliers)
    - gender (string, categorical)
    - date (datetime)
    """
    np.random.seed(42)
    rows = 100
    
    # ID
    ids = list(range(1, rows + 1))
    
    # Name
    names = [f"User_{i}" for i in range(1, rows + 1)]
    
    # Age (with some NaNs)
    ages = np.random.randint(18, 65, size=rows).astype(float)
    ages[10] = np.nan
    ages[25] = np.nan
    ages[50] = np.nan
    
    # Salary (with some clear outliers)
    salaries = np.random.normal(50000, 10000, size=rows)
    salaries[5] = 150000.0  # High outlier
    salaries[15] = -5000.0  # Low outlier
    salaries[50] = 200000.0 # High outlier
    
    # Gender (categorical)
    genders = np.random.choice(["Male", "Female", None], size=rows, p=[0.45, 0.45, 0.1])
    
    # Date (datetime)
    dates = pd.date_range(start="2026-01-01", periods=rows, freq="D")
    
    df = pd.DataFrame({
        "id": ids,
        "name": names,
        "age": ages,
        "salary": salaries,
        "gender": genders,
        "date": dates
    })
    
    # Ensure some duplicate rows are added
    # Duplicate row 20 and 30
    df.iloc[30] = df.iloc[20].copy()
    df.iloc[40] = df.iloc[20].copy()
    
    return df

@pytest.fixture
def create_temp_file(sample_dataframe):
    """
    Helper to save the sample dataframe to different formats.
    """
    files_created = []

    def _create(format_ext: str, df: pd.DataFrame = None) -> str:
        if df is None:
            df = sample_dataframe
            
        filename = f"test_data_{os.urandom(4).hex()}{format_ext}"
        filepath = os.path.join(settings.UPLOADS_DIR, filename)
        
        if format_ext == ".csv":
            df.to_csv(filepath, index=False)
        elif format_ext in [".xlsx", ".xls"]:
            df.to_excel(filepath, index=False, engine="openpyxl")
        elif format_ext == ".json":
            df.to_json(filepath, orient="records", date_format="iso")
        elif format_ext == ".parquet":
            # Parquet requires strings or numeric types, but date types are fine.
            # Handle gender None by casting it to string or let pyarrow handle it
            temp_df = df.copy()
            # Convert list/dict or mixed types if any to string
            temp_df["gender"] = temp_df["gender"].astype(str)
            temp_df.to_parquet(filepath, index=False, engine="pyarrow")
        else:
            raise ValueError(f"Unsupported format extension: {format_ext}")
            
        files_created.append(filepath)
        return filepath

    yield _create

    # Cleanup any custom files created in this fixture
    for f in files_created:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
