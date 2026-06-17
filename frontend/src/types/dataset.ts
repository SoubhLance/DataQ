export interface ColumnInspect {
  name: string;
  dtype: string;
  missing: number;
  missing_percent: number;
  unique: number;
  cardinality: number;
}

export interface InspectResponse {
  shape: [number, number];
  columns: ColumnInspect[];
  numeric_columns: string[];
  categorical_columns: string[];
  memory_usage_mb: number;
}

export interface QualityResponse {
  score: number;
  warnings: string[];
}

export interface CorrelationPair {
  column1: string;
  column2: string;
  correlation: number;
  recommendation: string;
}

export interface CorrelationResponse {
  matrix: Record<string, Record<string, number | null>>;
  highly_correlated: CorrelationPair[];
}

export interface ImbalanceResponse {
  ratio: string;
  imbalanced: boolean;
  class_counts: Record<string, number>;
}

export interface MissingColumnDetail {
  column: string;
  missing: number;
  percent: number;
  recommended: string;
}

export interface MissingCheckResponse {
  columns: MissingColumnDetail[];
}

export interface OutlierColumnDetail {
  column: string;
  outliers: number;
  percentage: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface OutlierCheckResponse {
  method: string;
  columns: OutlierColumnDetail[];
}

export interface PreviewRow {
  [key: string]: any;
}

export interface PreviewResponse {
  affected_rows: number;
  sample_before: PreviewRow[];
  sample_after: PreviewRow[];
}
