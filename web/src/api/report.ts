import { API_BASE_URL, apiBlobRequest, apiRequest } from "./client";
import type { JobCreateResponse } from "../types/jobs";
import type { ReportRequest, ReportResponse } from "../types/report";

export function createReport(
  datasetId: string,
  request: ReportRequest,
): Promise<ReportResponse> {
  return apiRequest<ReportResponse>(`/datasets/${encodeURIComponent(datasetId)}/report`, {
    body: { ...request },
    method: "POST",
  });
}

export function createReportJob(
  datasetId: string,
  request: ReportRequest,
): Promise<JobCreateResponse> {
  return apiRequest<JobCreateResponse>(`/datasets/${encodeURIComponent(datasetId)}/report?async=true`, {
    body: { ...request },
    method: "POST",
  });
}

export function getReportDownloadUrl(datasetId: string, reportId: string): string {
  return `${API_BASE_URL}/datasets/${encodeURIComponent(datasetId)}/reports/${encodeURIComponent(reportId)}/download`;
}

export async function downloadReport(datasetId: string, reportId: string): Promise<Blob> {
  return apiBlobRequest(
    `/datasets/${encodeURIComponent(datasetId)}/reports/${encodeURIComponent(reportId)}/download`,
    { method: "GET" },
  );
}
