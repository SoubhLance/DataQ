import pandas as pd
from typing import List, Dict, Any
from app.models.session_model import SessionState
from app.core.profiler import DatasetProfiler
from app.schemas.missing_schema import MissingColumnDetail

class RecommendationService:
    """
    Automated recommendation engine that inspects missing values, outliers,
    and categorical properties to propose optimal cleaning methods.
    """
    @staticmethod
    def get_missing_recommendations(session: SessionState) -> List[MissingColumnDetail]:
        """
        Produce missing value treatment recommendations based on column type and missing percentage.
        - Numeric < 20%: median
        - Numeric 20% - 60%: mean
        - Numeric >= 60%: drop
        - Categorical < 60%: mode
        - Categorical >= 60%: drop
        """
        df = session.current_df
        total_rows = len(df)
        profiler = DatasetProfiler(df)
        recommendations = []
        
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            if missing_count == 0:
                continue
                
            missing_pct = (missing_count / total_rows) * 100 if total_rows > 0 else 0.0
            
            # Recommendation rules
            if col in profiler.numeric_columns:
                if missing_pct < 20.0:
                    rec = "median"
                elif missing_pct < 60.0:
                    rec = "mean"
                else:
                    rec = "drop"
            else:
                # Categorical / Other
                if missing_pct < 60.0:
                    rec = "mode"
                else:
                    rec = "drop"
                    
            recommendations.append(
                MissingColumnDetail(
                    column=col,
                    missing=missing_count,
                    percent=round(missing_pct, 2),
                    recommended=rec
                )
            )
            
        return recommendations

    @staticmethod
    def get_encoding_recommendations(session: SessionState) -> List[Dict[str, Any]]:
        """
        Recommend encoding techniques for categorical columns.
        - Low cardinality (<= 10 categories): One-Hot Encoding (prevents order bias)
        - High cardinality (> 10 categories): Label Encoding (avoids dimension explosion)
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        recommendations = []
        
        for col in profiler.categorical_columns:
            unique_count = df[col].nunique(dropna=True)
            
            if unique_count <= 10:
                rec = "onehot"
                reason = f"Low cardinality ({unique_count} unique values). One-hot encoding creates dummy variables."
            else:
                rec = "label"
                reason = f"High cardinality ({unique_count} unique values). Label encoding avoids dimension explosion."
                
            recommendations.append({
                "column": col,
                "unique_values": unique_count,
                "recommended": rec,
                "reason": reason
            })
            
        return recommendations

    @staticmethod
    def get_outlier_recommendations(session: SessionState) -> List[Dict[str, Any]]:
        """
        Suggest outlier treatment based on standard IQR checks.
        - Outliers detected < 5%: IQR removal (remove)
        - Outliers detected 5% - 15%: IQR capping (cap)
        - Outliers > 15%: keep (potential distribution property, capping could skew results)
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        total_rows = len(df)
        recommendations = []
        
        for col in profiler.numeric_columns:
            series = df[col].dropna()
            if len(series) < 5:
                continue
                
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = ((series < lower) | (series > upper)).sum()
            if outliers == 0:
                continue
                
            outlier_pct = (outliers / total_rows) * 100 if total_rows > 0 else 0.0
            
            if outlier_pct < 5.0:
                rec_action = "remove"
                reason = f"Low outlier density ({outlier_pct:.2f}%). Safe to drop outlier rows."
            elif outlier_pct <= 15.0:
                rec_action = "cap"
                reason = f"Moderate outlier density ({outlier_pct:.2f}%). Recommend capping values to upper/lower bounds."
            else:
                rec_action = "keep"
                reason = f"High outlier density ({outlier_pct:.2f}%). Outliers represent natural distribution shape. Keep them."
                
            recommendations.append({
                "column": col,
                "outliers": int(outliers),
                "percentage": round(outlier_pct, 2),
                "recommended_method": "iqr",
                "recommended_action": rec_action,
                "reason": reason
            })
            
        return recommendations
