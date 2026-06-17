import os
import json
from datetime import datetime
from typing import Dict, Any
from app.models.session_model import SessionState
from app.config.settings import settings
from app.services.statistics_service import StatisticsService
from app.services.duplicate_service import DuplicateService
from app.services.outlier_service import OutlierService
from app.services.recommendation_service import RecommendationService
from app.config.constants import OutlierMethod

class ReportService:
    """
    Service responsible for compiling detailed dataset reports.
    """
    @staticmethod
    def generate_json_report(session: SessionState) -> Dict[str, Any]:
        """
        Generate a structured JSON compilation of the dataset's quality profiles.
        """
        # 1. Structure Summary
        summary = {
            "session_id": session.session_id,
            "filename": session.filename,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
            "shape": [session.rows, session.columns],
            "total_rows": session.rows,
            "total_columns": session.columns,
            "operations_count": len(session.operations)
        }
        
        # 2. Duplicate Check
        dup_stats = DuplicateService.detect_duplicates(session)
        duplicates = {
            "duplicate_rows": dup_stats.duplicate_rows,
            "duplicate_percent": dup_stats.duplicate_percent
        }
        
        # 3. Missing Check
        missing_recs = RecommendationService.get_missing_recommendations(session)
        missing = {
            "columns_with_missing": len(missing_recs),
            "details": [
                {
                    "column": rec.column,
                    "missing_count": rec.missing,
                    "percentage": rec.percent,
                    "recommended_strategy": rec.recommended
                } for rec in missing_recs
            ]
        }
        
        # 4. Outliers Check (Use IQR by default)
        outlier_res = OutlierService.detect_outliers(session, OutlierMethod.IQR)
        columns_with_outliers = [c for c in outlier_res.columns if c.outliers > 0]
        outliers = {
            "columns_with_outliers": len(columns_with_outliers),
            "details": [
                {
                    "column": col.column,
                    "outliers_count": col.outliers,
                    "percentage": col.percentage,
                    "lower_bound": col.lower_bound,
                    "upper_bound": col.upper_bound
                } for col in columns_with_outliers
            ]
        }
        
        # 5. Quality Score
        quality = StatisticsService.calculate_quality_score(session)
        quality_score = {
            "score": quality.score,
            "warnings": quality.warnings
        }
        
        report = {
            "summary": summary,
            "duplicates": duplicates,
            "missing": missing,
            "outliers": outliers,
            "quality_score": quality_score
        }
        
        # Write to reports storage folder
        report_filename = f"{session.session_id}_report.json"
        report_filepath = os.path.join(settings.REPORTS_DIR, report_filename)
        with open(report_filepath, "w") as f:
            json.dump(report, f, indent=2)
            
        return report
