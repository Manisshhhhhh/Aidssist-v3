import { AlertCircle, CheckCircle2, Clock3, Loader2, XCircle } from "lucide-react";

import type { JobResponse } from "../../types/jobs";
import { JobProgressBar } from "./JobProgressBar";

type JobStatusCardProps = {
  job: JobResponse | null;
  error?: string | null;
  title?: string;
};

export function JobStatusCard({ error, job, title = "Background job" }: JobStatusCardProps) {
  if (error) {
    return (
      <div className="rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-on-surface">
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 shrink-0 text-danger" size={18} aria-hidden="true" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
        Preparing job status.
      </div>
    );
  }

  const Icon = iconForStatus(job.status);

  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Icon className={iconClassForStatus(job.status)} size={19} aria-hidden="true" />
          <div>
            <p className="font-semibold text-on-surface">{title}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.14em] text-on-surface-muted">
              {job.job_type} · {job.status}
            </p>
          </div>
        </div>
        <span className="font-mono text-xs text-on-surface-muted">{job.progress}%</span>
      </div>
      <div className="mt-4">
        <JobProgressBar progress={job.progress} />
      </div>
      {job.error_message ? <p className="mt-3 text-sm text-danger">{job.error_message}</p> : null}
    </div>
  );
}

function iconForStatus(status: JobResponse["status"]) {
  if (status === "succeeded") return CheckCircle2;
  if (status === "failed") return XCircle;
  if (status === "cancelled") return XCircle;
  if (status === "running") return Loader2;
  return Clock3;
}

function iconClassForStatus(status: JobResponse["status"]): string {
  const base = "mt-0.5 shrink-0";
  if (status === "succeeded") return `${base} text-success`;
  if (status === "failed" || status === "cancelled") return `${base} text-danger`;
  if (status === "running") return `${base} animate-spin text-primary-light`;
  return `${base} text-on-surface-muted`;
}
