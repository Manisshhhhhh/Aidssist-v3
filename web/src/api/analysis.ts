import { apiRequest } from "./client";
import { isReachabilityError } from "./errors";
import type { AnalysisResponse } from "../types/analysis";

export async function analyzeDataset(datasetId: string): Promise<AnalysisResponse> {
  const path = `/datasets/${encodeURIComponent(datasetId)}/analyze`;
  let lastError: unknown;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      return await apiRequest<AnalysisResponse>(path, { method: "POST" });
    } catch (error) {
      lastError = error;
      if (!isReachabilityError(error) || attempt === 2) {
        break;
      }
      await delay(750 * (attempt + 1));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Unable to analyze this dataset.");
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}
