export type ChartType =
  | "bar"
  | "line"
  | "scatter"
  | "histogram"
  | "box"
  | "pie"
  | "heatmap"
  | "area";

export type ChartTimeRange = "all" | "1d" | "1w" | "1m" | "1q" | "1y" | "3y" | "5y";

export interface ChartDataPoint {
  x?: string | number | null;
  y?: string | number | null;
  value?: number | null;
  label?: string | null;
  bin_start?: number | null;
  bin_end?: number | null;
  min?: number | null;
  q1?: number | null;
  median?: number | null;
  q3?: number | null;
  max?: number | null;
  mean?: number | null;
  outlier_count?: number | null;
}

export interface ChartDataMetadata {
  x_label: string;
  y_label?: string | null;
  aggregation?: string | null;
  row_count: number;
  [key: string]: string | number | boolean | null | undefined;
}

export interface ChartDataResponse {
  dataset_id: string;
  chart_id: string;
  title: string;
  description: string;
  chart_type: ChartType;
  x: string;
  y: string | null;
  series: string | null;
  data: ChartDataPoint[];
  metadata: ChartDataMetadata;
  created_at: string;
}
