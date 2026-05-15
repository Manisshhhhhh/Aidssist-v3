export type AiSummaryTone = "executive" | "analyst" | "concise";
export type AiSummaryFormat = "bullets" | "narrative";

export interface AiSummaryRequest {
  include_forecast: boolean;
  include_charts: boolean;
  tone: AiSummaryTone;
  format: AiSummaryFormat;
}

export interface AiSummaryGrounding {
  used_analysis: boolean;
  used_forecast: boolean;
  used_charts: boolean;
  raw_rows_sent: boolean;
}

export interface AiSummaryResponse {
  dataset_id: string;
  summary_id: string;
  provider: string;
  model: string;
  summary: string;
  grounding: AiSummaryGrounding;
  warnings: string[];
  created_at: string;
}
