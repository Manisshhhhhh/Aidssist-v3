import { apiRequest } from "./client";
import type { ForecastRequest, ForecastResponse } from "../types/forecast";

export function createForecast(
  datasetId: string,
  request: ForecastRequest,
): Promise<ForecastResponse> {
  return apiRequest<ForecastResponse>(`/datasets/${encodeURIComponent(datasetId)}/forecast`, {
    body: { ...request },
    method: "POST",
  });
}
