import { apiRequest } from "./client";
import type { ChatRequest, ChatResponse } from "../types/chat";

export function askDataset(datasetId: string, request: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>(`/datasets/${encodeURIComponent(datasetId)}/chat`, {
    body: { ...request },
    method: "POST",
  });
}
