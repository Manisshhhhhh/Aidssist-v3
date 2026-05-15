import { apiRequest } from "./client";
import type { JobListResponse, JobResponse, JobStatus, JobType } from "../types/jobs";

export type JobListParams = {
  workspaceId?: number | null;
  status?: JobStatus;
  jobType?: JobType;
  limit?: number;
};

export function getJob(jobId: string): Promise<JobResponse> {
  return apiRequest<JobResponse>(`/jobs/${encodeURIComponent(jobId)}`);
}

export function listJobs(params: JobListParams = {}): Promise<JobListResponse> {
  const search = new URLSearchParams();
  if (params.workspaceId) search.set("workspace_id", String(params.workspaceId));
  if (params.status) search.set("status", params.status);
  if (params.jobType) search.set("job_type", params.jobType);
  if (params.limit) search.set("limit", String(params.limit));
  const query = search.toString();
  return apiRequest<JobListResponse>(`/jobs${query ? `?${query}` : ""}`);
}

export function cancelJob(jobId: string): Promise<JobResponse> {
  return apiRequest<JobResponse>(`/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
  });
}
