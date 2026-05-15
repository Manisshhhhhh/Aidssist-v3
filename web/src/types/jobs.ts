export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";
export type JobType = "analysis" | "forecast" | "report" | "filesystem_sync" | "future_reserved";

export interface JobCreateResponse {
  job_id: string;
  job_type: JobType;
  status: JobStatus;
  progress: number;
  status_url: string;
  created_at: string;
}

export interface JobResponse {
  job_id: string;
  job_type: JobType;
  status: JobStatus;
  progress: number;
  dataset_id?: string | null;
  workspace_id?: number | null;
  output?: unknown;
  error_message?: string | null;
  attempts: number;
  max_attempts: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface JobListResponse {
  jobs: JobResponse[];
}
