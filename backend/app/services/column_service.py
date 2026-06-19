import pandas as pd
from typing import List, Dict, Any
from sklearn.preprocessing import LabelEncoder
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.config.constants import EncodingMethod, DataType
from app.exceptions.dataset_exceptions import ColumnNotFound, OperationError
from app.utils.validators import validate_columns_exist, validate_column_dtype_compatibility
from app.schemas.column_schema import ColumnEncodePreviewResponse

class ColumnService:
    """
    Service responsible for column level actions: dropping, renaming,
    data type casting, and encoding (Label / One-Hot).
    """
    @staticmethod
    def get_columns(session: SessionState) -> List[str]:
        """Get column names list."""
        return list(session.current_df.columns)

    @staticmethod
    def drop_columns(session: SessionState, columns: List[str]) -> None:
        """Drop columns from dataset."""
        df = session.current_df.copy()
        validate_columns_exist(df, columns)
        
        df = df.drop(columns=columns)
        
        op = Operation(
            type="column_drop",
            params={"columns": columns},
            generated_code=f"df = df.drop(columns={columns})",
            description=f"Dropped column(s): {', '.join(columns)}"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def rename_column(session: SessionState, old_name: str, new_name: str) -> None:
        """Rename a column in the dataset."""
        df = session.current_df.copy()
        validate_columns_exist(df, [old_name])
        
        df = df.rename(columns={old_name: new_name})
        
        op = Operation(
            type="column_rename",
            params={"old_name": old_name, "new_name": new_name},
            generated_code=f"df = df.rename(columns={{'{old_name}': '{new_name}'}})",
            description=f"Renamed column '{old_name}' to '{new_name}'"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def change_dtype(session: SessionState, column: str, new_dtype: DataType) -> None:
        """Cast column to specified target data type."""
        df = session.current_df.copy()
        validate_column_dtype_compatibility(df, column, new_dtype)
        
        # Cast values
        target = new_dtype.lower()
        if target == DataType.INT:
            df[column] = pd.to_numeric(df[column]).astype("Int64")
            code = f"df['{column}'] = pd.to_numeric(df['{column}']).astype('Int64')"
        elif target == DataType.FLOAT:
            df[column] = pd.to_numeric(df[column]).astype(float)
            code = f"df['{column}'] = pd.to_numeric(df['{column}']).astype(float)"
        elif target == DataType.STRING:
            df[column] = df[column].astype(str)
            code = f"df['{column}'] = df['{column}'].astype(str)"
        elif target == DataType.DATETIME:
            df[column] = pd.to_datetime(df[column])
            code = f"df['{column}'] = pd.to_datetime(df['{column}'])"
        else:
            raise OperationError("Casting", f"Unsupported cast datatype: {new_dtype}")
            
        op = Operation(
            type="column_cast",
            params={"column": column, "new_dtype": new_dtype.value},
            generated_code=code,
            description=f"Casted column '{column}' to type '{new_dtype.value}'"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def _label_encode_series(series: pd.Series) -> pd.Series:
        """
        Fit-transform a Pandas Series using LabelEncoder, preserving original NaN/None values.
        Does not convert NaN to "nan" category.
        """
        res = series.copy()
        non_null_mask = res.notna()
        if non_null_mask.any():
            le = LabelEncoder()
            encoded = le.fit_transform(res[non_null_mask].astype(str))
            res = res.astype(object)
            res.loc[non_null_mask] = encoded
            res = pd.to_numeric(res, errors='coerce')
        return res

    @staticmethod
    def preview_encoding(session: SessionState, column: str, method: EncodingMethod) -> ColumnEncodePreviewResponse:
        """
        Preview encoding changes on the first 10 rows.
        """
        df = session.current_df
        validate_columns_exist(df, [column])
        
        df_temp = df.head(10).copy()
        affected_count = len(df)
        
        sample_before = df_temp[[column]].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        if method == EncodingMethod.LABEL:
            df_temp[column] = ColumnService._label_encode_series(df_temp[column])
            sample_after = df_temp[[column]].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
            
        elif method == EncodingMethod.ONEHOT:
            # One-hot encode the column
            dummies = pd.get_dummies(df_temp[[column]], columns=[column], prefix=column, dtype=int)
            sample_after = dummies.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
            
        return ColumnEncodePreviewResponse(
            affected_rows=affected_count,
            sample_before=sample_before,
            sample_after=sample_after
        )

    @staticmethod
    def apply_encoding(session: SessionState, column: str, method: EncodingMethod) -> None:
        """
        Encode column (Label or One-Hot), write generated code snippet, and update session.
        """
        df = session.current_df.copy()
        validate_columns_exist(df, [column])
        
        if method == EncodingMethod.LABEL:
            df[column] = ColumnService._label_encode_series(df[column])
            
            code = (
                f"from sklearn.preprocessing import LabelEncoder\n"
                f"le_{column} = LabelEncoder()\n"
                f"mask_{column} = df['{column}'].notna()\n"
                f"if mask_{column}.any():\n"
                f"    df.loc[mask_{column}, '{column}'] = le_{column}.fit_transform(df.loc[mask_{column}, '{column}'].astype(str))\n"
                f"    df['{column}'] = pd.to_numeric(df['{column}'], errors='ignore')"
            )
            
        elif method == EncodingMethod.ONEHOT:
            # Drop the original column and create dummy vars
            df = pd.get_dummies(df, columns=[column], prefix=column, dtype=int)
            code = f"df = pd.get_dummies(df, columns=['{column}'], prefix='{column}', dtype=int)"
            
        else:
            raise OperationError("Encoding", f"Unsupported encoding method: {method}")
            
        op = Operation(
            type="column_encode",
            params={"column": column, "method": method.value},
            generated_code=code,
            description=f"Encoded column '{column}' using {method.value} encoding"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def replay_column_op(df: pd.DataFrame, op_type: str, params: Dict[str, Any]) -> pd.DataFrame:
        """Replay column operation on a dataframe."""
        df_copy = df.copy()
        
        if op_type == "column_drop":
            return df_copy.drop(columns=params["columns"])
            
        elif op_type == "column_rename":
            return df_copy.rename(columns={params["old_name"]: params["new_name"]})
            
        elif op_type == "column_cast":
            col = params["column"]
            target = params["new_dtype"].lower()
            if target == "int":
                df_copy[col] = pd.to_numeric(df_copy[col]).astype("Int64")
            elif target == "float":
                df_copy[col] = pd.to_numeric(df_copy[col]).astype(float)
            elif target == "string":
                df_copy[col] = df_copy[col].astype(str)
            elif target == "datetime":
                df_copy[col] = pd.to_datetime(df_copy[col])
            return df_copy
            
        elif op_type == "column_encode":
            col = params["column"]
            method = EncodingMethod(params["method"])
            if method == EncodingMethod.LABEL:
                df_copy[col] = ColumnService._label_encode_series(df_copy[col])
            elif method == EncodingMethod.ONEHOT:
                df_copy = pd.get_dummies(df_copy, columns=[col], prefix=col, dtype=int)
            return df_copy
            
        return df_copy
