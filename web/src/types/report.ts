export type ReportFormat = "html" | "json";

export interface ReportRequest {
  format: ReportFormat;
  include_forecast: boolean;
  include_charts: boolean;
  include_chat_summary: boolean;
  include_ai_summary: boolean;
}

export interface ReportResponse {
  dataset_id: string;
  report_id: string;
  format: ReportFormat;
  filename: string;
  download_url: string;
  created_at: string;
}
