export interface ReportSummary {
  session_id: string;
  filename: string;
  created_at: string;
  last_accessed: string;
  shape: [number, number];
  total_rows: number;
  total_columns: number;
  operations_count: number;
}

export interface ReportDuplicates {
  duplicate_rows: number;
  duplicate_percent: number;
}

export interface ReportMissingDetail {
  column: string;
  missing_count: number;
  percentage: number;
  recommended_strategy: string;
}

export interface ReportMissing {
  columns_with_missing: number;
  details: ReportMissingDetail[];
}

export interface ReportOutlierDetail {
  column: string;
  outliers_count: number;
  percentage: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface ReportOutliers {
  columns_with_outliers: number;
  details: ReportOutlierDetail[];
}

export interface ReportQualityScore {
  score: number;
  warnings: string[];
}

export interface ReportResponse {
  summary: ReportSummary;
  duplicates: ReportDuplicates;
  missing: ReportMissing;
  outliers: ReportOutliers;
  quality_score: ReportQualityScore;
}
