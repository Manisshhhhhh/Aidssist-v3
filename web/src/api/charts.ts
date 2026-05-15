import { apiRequest } from "./client";
import type { ChartDataResponse, ChartTimeRange } from "../types/charts";

export function getChartData(
  datasetId: string,
  chartId: string,
  timeRange: ChartTimeRange = "all",
): Promise<ChartDataResponse> {
  const query = timeRange === "all" ? "" : `?time_range=${encodeURIComponent(timeRange)}`;
  return apiRequest<ChartDataResponse>(
    `/datasets/${encodeURIComponent(datasetId)}/charts/${encodeURIComponent(chartId)}/data${query}`,
  );
}
