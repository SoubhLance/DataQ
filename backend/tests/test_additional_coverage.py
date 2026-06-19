import os
import pytest
import pandas as pd
import numpy as np
import anyio
from unittest.mock import AsyncMock, MagicMock, patch
from app.exceptions.session_exceptions import SessionExpired
from app.exceptions.validation_exceptions import FileTooLarge, UnsupportedFileType, ValidationException
from app.exceptions.dataset_exceptions import ColumnNotFound, InvalidDtype, EmptyDataset, OperationError
from app.utils.validators import validate_uploaded_file, validate_columns_exist, validate_column_dtype_compatibility, validate_file_content
from app.services.missing_service import MissingService
from app.config.constants import MissingStrategy, OutlierMethod, OutlierAction
from app.models.session_model import SessionState
from app.services.outlier_service import OutlierService
from app.services.statistics_service import StatisticsService
from app.utils.file_utils import load_file_to_dataframe, save_dataframe_to_file, cleanup_session_files
from app.utils.websocket_manager import ConnectionManager

@pytest.mark.unit
def test_exceptions_coverage():
    # SessionExpired exception property check
    with pytest.raises(SessionExpired):
        raise SessionExpired("session_exp")
    
    # FileTooLarge exception property check
    with pytest.raises(FileTooLarge):
        raise FileTooLarge(200, 100)

@pytest.mark.unit
def test_websocket_broadcast_exception():
    async def run_test():
        manager = ConnectionManager()
        ws_mock = MagicMock()
        ws_mock.send_json = AsyncMock(side_effect=Exception("mock send error"))
        ws_mock.accept = AsyncMock()
        
        # Connect
        await manager.connect("session_x", ws_mock)
        
        # Broadcast to it (triggers exception and disconnect)
        await manager.broadcast_to_session("session_x", {"msg": "hello"})
        
        # Verify it is disconnected/removed
        assert "session_x" not in manager.active_connections

    anyio.run(run_test)

@pytest.mark.unit
def test_validators_coverage(tmp_path):
    # 1. validate_uploaded_file size limit
    from app.config.settings import settings
    original_limit = settings.MAX_UPLOAD_SIZE
    try:
        settings.MAX_UPLOAD_SIZE = 10
        with pytest.raises(FileTooLarge):
            validate_uploaded_file("test.csv", 20)
    finally:
        settings.MAX_UPLOAD_SIZE = original_limit

    # 2. validate_columns_exist
    df = pd.DataFrame({"A": [1, 2]})
    with pytest.raises(ColumnNotFound):
        validate_columns_exist(df, ["B"])

    # 3. validate_column_dtype_compatibility
    with pytest.raises(ColumnNotFound):
        validate_column_dtype_compatibility(df, "B", "int")
    
    # Empty column case
    df_empty = pd.DataFrame({"A": [np.nan, np.nan]})
    validate_column_dtype_compatibility(df_empty, "A", "int")  # returns early
    
    # String target case
    validate_column_dtype_compatibility(df, "A", "string")

    # 4. validate_file_content check error paths
    # Parquet with invalid signature
    parquet_path = os.path.join(tmp_path, "test.parquet")
    with open(parquet_path, "wb") as f:
        f.write(b"NOT_PAR1")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(parquet_path, "test.parquet", "application/octet-stream")
    assert "missing 'PAR1'" in str(exc.value)

    # Parquet with invalid content type
    with open(parquet_path, "wb") as f:
        f.write(b"PAR1_headers")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(parquet_path, "test.parquet", "image/png")
    assert "Invalid Content-Type for Parquet" in str(exc.value)

    # Excel with invalid signature
    excel_path = os.path.join(tmp_path, "test.xlsx")
    with open(excel_path, "wb") as f:
        f.write(b"NOT_ZIP")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(excel_path, "test.xlsx", "application/zip")
    assert "missing ZIP archive" in str(exc.value)

    # Excel with invalid content type
    with open(excel_path, "wb") as f:
        f.write(b"PK\x03\x04_headers")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(excel_path, "test.xlsx", "image/png")
    assert "Invalid Content-Type for Excel" in str(exc.value)

    # JSON with invalid signature
    json_path = os.path.join(tmp_path, "test.json")
    with open(json_path, "wb") as f:
        f.write(b"NOT_JSON")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(json_path, "test.json", "application/json")
    assert "missing '{' or '['" in str(exc.value)

    # JSON with invalid content type
    with open(json_path, "wb") as f:
        f.write(b"{}")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(json_path, "test.json", "image/png")
    assert "Invalid Content-Type for JSON" in str(exc.value)

    # CSV containing binary null bytes
    csv_path = os.path.join(tmp_path, "test.csv")
    with open(csv_path, "wb") as f:
        f.write(b"a,b,c\x00d")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(csv_path, "test.csv", "text/csv")
    assert "binary null bytes" in str(exc.value)

    # CSV with zip/parquet signature
    with open(csv_path, "wb") as f:
        f.write(b"PK\x03\x04")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(csv_path, "test.csv", "text/csv")
    assert "binary zip/parquet signature" in str(exc.value)

    # CSV with invalid content type
    with open(csv_path, "wb") as f:
        f.write(b"a,b,c")
    with pytest.raises(ValidationException) as exc:
        validate_file_content(csv_path, "test.csv", "image/png")
    assert "Invalid Content-Type for CSV" in str(exc.value)

    # Unsupported extension
    with pytest.raises(UnsupportedFileType):
        validate_file_content(csv_path, "test.png", "image/png")

    # Non-existent file
    with pytest.raises(ValidationException) as exc:
        validate_file_content("non_existent_file_xyz.csv", "test.csv", "text/csv")
    assert "Failed to read file" in str(exc.value)

@pytest.mark.unit
def test_missing_service_coverage():
    initial_df = pd.DataFrame({"A": [1, 2, 3]})
    session = SessionState(session_id="session_123", filename="dummy.csv", df=initial_df)
    
    # 1. Preview imputation with 0 missing values
    res = MissingService.preview_imputation(session, "A", MissingStrategy.MEAN)
    assert res.affected_rows == 0
    assert len(res.sample_before) == 0

    # 2. Preview imputation with strategy DROP
    df_missing = pd.DataFrame({"A": [1.0, np.nan, 3.0]})
    session.update_dataframe(df_missing)
    res_drop = MissingService.preview_imputation(session, "A", MissingStrategy.DROP)
    assert res_drop.affected_rows == 1
    assert len(res_drop.sample_after) == 0

    # 3. Apply imputation with strategy DROP
    MissingService.apply_imputation(session, "A", MissingStrategy.DROP)
    assert len(session.current_df) == 2

    # 4. _calculate_impute_value exception paths
    # MEAN on non-numeric
    s_non_numeric = pd.Series(["A", "B", np.nan])
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_non_numeric, MissingStrategy.MEAN)
    assert "Mean can only be applied" in str(exc.value)

    # MEDIAN on non-numeric
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_non_numeric, MissingStrategy.MEDIAN)
    assert "Median can only be applied" in str(exc.value)

    # MODE on empty series
    s_empty = pd.Series([], dtype=object)
    assert MissingService._calculate_impute_value(s_empty, MissingStrategy.MODE) is None

    # CONSTANT when constant_value is None
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(df_missing["A"], MissingStrategy.CONSTANT, None)
    assert "requires a non-null constant_value" in str(exc.value)

    # CONSTANT on integer column with float value with fractional parts
    s_int = pd.Series([1, 2, np.nan], dtype="Int64")
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_int, MissingStrategy.CONSTANT, "2.5")
    assert "fractional part" in str(exc.value)

    # CONSTANT on integer column with non-numeric value
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_int, MissingStrategy.CONSTANT, "abc")
    assert "not convertible to integer" in str(exc.value)

    # CONSTANT on float column with non-numeric value
    s_float = pd.Series([1.0, 2.0, np.nan])
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_float, MissingStrategy.CONSTANT, "abc")
    assert "not convertible to float" in str(exc.value)

    # CONSTANT on boolean column
    s_bool = pd.Series([True, False, np.nan], dtype="boolean")
    for tr in ["yes", "true", "1", "y", "t"]:
        assert MissingService._calculate_impute_value(s_bool, MissingStrategy.CONSTANT, tr) is True
    for fa in ["no", "false", "0", "f", "n"]:
        assert MissingService._calculate_impute_value(s_bool, MissingStrategy.CONSTANT, fa) is False
    with pytest.raises(OperationError) as exc:
        MissingService._calculate_impute_value(s_bool, MissingStrategy.CONSTANT, "invalid-bool")
    assert "not convertible to boolean" in str(exc.value)

    # CONSTANT on object column
    s_obj = pd.Series(["hello", "world", np.nan], dtype=object)
    assert MissingService._calculate_impute_value(s_obj, MissingStrategy.CONSTANT, 123) == "123"

    # Unknown imputation strategy
    with pytest.raises(OperationError):
        MissingService._calculate_impute_value(df_missing["A"], "unknown_strategy")

@pytest.mark.unit
def test_outlier_service_coverage():
    df_small = pd.DataFrame({"A": [1.0, 2.0, 3.0, 4.0]})
    session = SessionState(session_id="session_outlier", filename="dummy.csv", df=df_small)
    
    # Scan on small dataset
    res_detect = OutlierService.detect_outliers(session, OutlierMethod.IQR)
    assert len(res_detect.columns) == 0
    
    # Preview treatment on small dataset
    res_prev = OutlierService.preview_treatment(session, "A", OutlierMethod.IQR, OutlierAction.REMOVE)
    assert res_prev.affected_rows == 0
    
    # Apply treatment on small dataset
    OutlierService.apply_treatment(session, "A", OutlierMethod.IQR, OutlierAction.REMOVE)
    assert "too few values" in session.operations[-1].generated_code

    # Replay outliers on small dataset
    df_rep = OutlierService.replay_outliers(df_small, "A", "iqr", "remove")
    assert len(df_rep) == 4

    # Series with enough values
    df_large = pd.DataFrame({"A": [1.0, 1.1, 1.2, 1.3, 100.0]})
    session.update_dataframe(df_large)
    
    # Preview treatment with KEEP
    res_keep = OutlierService.preview_treatment(session, "A", OutlierMethod.IQR, OutlierAction.KEEP)
    assert res_keep.affected_rows == 1
    assert res_keep.sample_before == res_keep.sample_after

    # Isolation Forest treatment - Remove
    session.update_dataframe(df_large.copy())
    OutlierService.apply_treatment(session, "A", OutlierMethod.ISOLATION_FOREST, OutlierAction.REMOVE)
    assert "IsolationForest" in session.operations[-1].generated_code

    # Isolation Forest treatment - Cap
    session.update_dataframe(df_large.copy())
    OutlierService.apply_treatment(session, "A", OutlierMethod.ISOLATION_FOREST, OutlierAction.CAP)
    assert "clip" in session.operations[-1].generated_code
    
    # Replay Isolation Forest Cap
    df_cap_rep = OutlierService.replay_outliers(df_large, "A", "iforest", "cap")
    assert df_cap_rep["A"].max() < 100.0

    # Z-SCORE with std = 0
    s_const = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0])
    mask, lower, upper = OutlierService._get_outlier_mask_and_bounds(s_const, OutlierMethod.ZSCORE)
    assert not mask.any()
    assert lower is None
    assert upper is None

    # Unknown outlier detection method
    mask_unk, lower_unk, upper_unk = OutlierService._get_outlier_mask_and_bounds(s_const, "unknown_method")
    assert not mask_unk.any()

@pytest.mark.unit
def test_statistics_service_coverage():
    df_empty_col = pd.DataFrame({"A": [np.nan, np.nan, np.nan]})
    session = SessionState(session_id="session_stats", filename="dummy.csv", df=df_empty_col)
    
    # 1. get_skewness_and_variance empty numeric column
    stats = StatisticsService.get_skewness_and_variance(session)
    assert stats["A"]["skewness"] == 0.0
    assert stats["A"]["variance"] == 0.0

    # 2. calculate_correlation_matrix with less than 2 numeric columns
    df_one_num = pd.DataFrame({"A": [1, 2, 3], "B": ["X", "Y", "Z"]})
    session.update_dataframe(df_one_num)
    res_corr = StatisticsService.calculate_correlation_matrix(session)
    assert res_corr.matrix == {}

    # 3. calculate_correlation_matrix with NaN pearson value (constant column)
    df_const_corr = pd.DataFrame({"A": [1, 2, 3], "B": [1, 1, 1]})
    session.update_dataframe(df_const_corr)
    res_const_corr = StatisticsService.calculate_correlation_matrix(session)
    assert res_const_corr.matrix["B"]["A"] is None or np.isnan(res_const_corr.matrix["B"]["A"])

    # 4. calculate_quality_score on empty dataset
    df_empty = pd.DataFrame()
    session.update_dataframe(df_empty)
    res_qual = StatisticsService.calculate_quality_score(session)
    assert res_qual.score == 0
    assert "Empty dataset" in res_qual.warnings[0]

    # 5. calculate_quality_score with high cardinality column
    df_cardinality = pd.DataFrame({
        "cat": [f"val_{i}" for i in range(20)],
        "num": list(range(20))
    })
    session.update_dataframe(df_cardinality)
    res_qual_card = StatisticsService.calculate_quality_score(session)
    assert any("high cardinality" in w for w in res_qual_card.warnings)

    # 6. check_class_imbalance target not in columns
    with pytest.raises(ColumnNotFound):
        StatisticsService.check_class_imbalance(session, "non_existent")

    # 7. check_class_imbalance with target column that has all NaN
    df_all_nan = pd.DataFrame({"target": [np.nan, np.nan]})
    session.update_dataframe(df_all_nan)
    res_imb = StatisticsService.check_class_imbalance(session, "target")
    assert res_imb.ratio == "0:0"
    assert not res_imb.imbalanced

    # 8. get_missing_heatmap_data with downsampling
    df_long = pd.DataFrame({"A": list(range(200))})
    session.update_dataframe(df_long)
    heatmap = StatisticsService.get_missing_heatmap_data(session, max_sample_rows=50)
    assert len(heatmap) == 50

    # 9. get_correlation_heatmap_data cases
    # > 300 columns
    df_300 = pd.DataFrame({f"col_{i}": [1, 2] for i in range(301)})
    session.update_dataframe(df_300)
    assert StatisticsService.get_correlation_heatmap_data(session) == []

    # < 2 numeric columns
    session.update_dataframe(df_one_num)
    assert StatisticsService.get_correlation_heatmap_data(session) == []

    # 10. get_distribution_histogram_data cases
    # Column not found
    with pytest.raises(ColumnNotFound):
        StatisticsService.get_distribution_histogram_data(session, "non_existent")
    # Non-numeric
    session.update_dataframe(df_one_num)
    assert StatisticsService.get_distribution_histogram_data(session, "B") == []

    # 11. get_boxplot_data cases
    # Column not found
    with pytest.raises(ColumnNotFound):
        StatisticsService.get_boxplot_data(session, "non_existent")
    # Non-numeric
    assert StatisticsService.get_boxplot_data(session, "B") == {}

@pytest.mark.unit
def test_file_utils_coverage(tmp_path):
    # 1. load_file_to_dataframe with unsupported extension
    invalid_file = os.path.join(tmp_path, "test.png")
    with open(invalid_file, "w") as f:
        f.write("abc")
    with pytest.raises(UnsupportedFileType):
        load_file_to_dataframe(invalid_file, "test.png")

    # 2. load_file_to_dataframe on a file with empty content
    empty_csv = os.path.join(tmp_path, "empty.csv")
    with open(empty_csv, "w") as f:
        pass
    with pytest.raises(OperationError) as exc:
        load_file_to_dataframe(empty_csv, "empty.csv")
    assert "Failed to parse file" in str(exc.value)

    # 3. load_file_to_dataframe on a file with only headers (empty rows)
    empty_rows_csv = os.path.join(tmp_path, "empty_rows.csv")
    with open(empty_rows_csv, "w") as f:
        f.write("col1,col2\n")
    with pytest.raises(EmptyDataset):
        load_file_to_dataframe(empty_rows_csv, "empty_rows.csv")

    # 4. save_dataframe_to_file check coercion format_ext without dot
    df = pd.DataFrame({"A": [1, 2]})
    save_path = os.path.join(tmp_path, "saved.csv")
    res_path = save_dataframe_to_file(df, save_path, "csv")
    assert res_path == save_path
    assert os.path.exists(save_path)

    # 5. save_dataframe_to_file unsupported format
    with pytest.raises(OperationError) as exc:
        save_dataframe_to_file(df, os.path.join(tmp_path, "saved.png"), "png")
    assert "Unsupported export format" in str(exc.value)

    # 6. save_dataframe_to_file causing write error (invalid directory path)
    with pytest.raises(OperationError) as exc:
        save_dataframe_to_file(df, "/invalid_dir_abc_123/file.csv", "csv")
    assert "Failed to write file" in str(exc.value)

    # 7. cleanup_session_files path traversal prevention
    class MockSession:
        def __init__(self):
            self.uploaded_filepath = "d:/outside_dir/test.csv"
            self.cleaned_filepaths = []
            self.report_filepaths = []
            
    mock_session = MockSession()
    cleanup_session_files(mock_session)

    # 8. cleanup_session_files deletion exception handling
    from app.config.settings import settings
    valid_path = os.path.join(settings.UPLOADS_DIR, "test_delete_fail.csv")
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    with open(valid_path, "w") as f:
        f.write("test")
        
    class MockSession2:
        def __init__(self):
            self.uploaded_filepath = valid_path
            self.cleaned_filepaths = []
            self.report_filepaths = []
            
    mock_session2 = MockSession2()
    with patch("os.remove", side_effect=Exception("mock remove error")):
        cleanup_session_files(mock_session2)
