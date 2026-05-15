export type ForecastFrequency = "auto" | "D" | "W" | "M";

export type ForecastModel = "auto" | "linear_regression" | "moving_average";

export interface ForecastRequest {
  date_column: string;
  target_column: string;
  periods: number;
  frequency: ForecastFrequency;
  model: ForecastModel;
}

export interface HistoricalPoint {
  date: string;
  value: number;
}

export interface ForecastPoint {
  date: string;
  predicted_value: number;
  lower_bound: number | null;
  upper_bound: number | null;
}

export interface ForecastMetrics {
  mae: number | null;
  rmse: number | null;
  mape: number | null;
}

export interface ForecastResponse {
  dataset_id: string;
  date_column: string;
  target_column: string;
  model_used: string;
  frequency: string;
  periods: number;
  historical_points: HistoricalPoint[];
  forecast_points: ForecastPoint[];
  metrics: ForecastMetrics;
  assumptions: string[];
  warnings: string[];
  created_at: string;
}
