import { apiRequest } from "./client";
import type { AiSummaryRequest, AiSummaryResponse } from "../types/llm";

export function createAiSummary(
  datasetId: string,
  request: AiSummaryRequest,
): Promise<AiSummaryResponse> {
  return apiRequest<AiSummaryResponse>(`/datasets/${encodeURIComponent(datasetId)}/ai-summary`, {
    method: "POST",
    body: { ...request },
  });
}
