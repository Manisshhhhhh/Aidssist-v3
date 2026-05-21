export type SemanticType = "numeric" | "categorical" | "datetime" | "boolean" | "text" | "unknown";

export type InsightSeverity = "info" | "low" | "medium" | "high";

export type ChartType =
  | "bar"
  | "line"
  | "scatter"
  | "histogram"
  | "box"
  | "pie"
  | "heatmap"
  | "area";

export interface TopValue {
  value: string | number | boolean | null;
  count: number;
  percent: number;
}

export interface ColumnStats {
  mean?: number | null;
  median?: number | null;
  min?: number | null;
  max?: number | null;
  std?: number | null;
  q1?: number | null;
  q3?: number | null;
  min_date?: string | null;
  max_date?: string | null;
  range_days?: number | null;
  invalid_parse_count?: number | null;
  invalid_parse_percent?: number | null;
  top_values?: TopValue[];
  average_length?: number | null;
  min_length?: number | null;
  max_length?: number | null;
}

export interface DataQualityIssue {
  type: string;
  severity: InsightSeverity;
  title: string;
  message: string;
  columns: string[];
  count?: number | null;
  percent?: number | null;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  semantic_type: SemanticType;
  missing_count: number;
  missing_percent: number;
  unique_count: number;
  unique_percent: number;
  sample_values: Array<string | number | boolean | null>;
  stats: ColumnStats;
}

export interface DataQuality {
  missing_cells: number;
  missing_percent: number;
  duplicate_rows: number;
  duplicate_percent: number;
  empty_columns: string[];
  constant_columns: string[];
  invalid_type_columns: string[];
  high_cardinality_columns: string[];
  date_parse_issue_columns: string[];
  outlier_columns: string[];
  issue_breakdown: DataQualityIssue[];
  quality_score: number;
}

export interface Correlation {
  column_a: string;
  column_b: string;
  correlation: number;
}

export interface Insight {
  type: string;
  severity: InsightSeverity;
  title: string;
  message: string;
  columns: string[];
}

export interface ChartConfig {
  aggregation?: "sum" | "mean" | "count";
  limit?: number;
  bins?: number;
  show_outliers?: boolean;
  trendline?: boolean;
  method?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface RecommendedChart {
  chart_id: string;
  title: string;
  description: string;
  chart_type: ChartType;
  x: string;
  y: string | null;
  series: string | null;
  priority: number;
  reason: string;
  config: ChartConfig;
}

export interface AnalysisResponse {
  dataset_id: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  quality: DataQuality;
  correlations: Correlation[];
  insights: Insight[];
  recommended_charts: RecommendedChart[];
  created_at: string;
}
