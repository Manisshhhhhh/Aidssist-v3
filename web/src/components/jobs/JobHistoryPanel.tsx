import { useCallback, useEffect, useState } from "react";

import { listJobs } from "../../api/jobs";
import type { JobResponse } from "../../types/jobs";
import { Button } from "../ui/Button";

type JobHistoryPanelProps = {
  workspaceId?: number | null;
};

export function JobHistoryPanel({ workspaceId }: JobHistoryPanelProps) {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    try {
      const response = await listJobs({ workspaceId, limit: 8 });
      setJobs(response.jobs);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load jobs.");
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  if (error) {
    return <p className="text-sm text-danger">{error}</p>;
  }

  if (jobs.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-on-surface">Recent jobs</p>
        <Button className="min-h-9 px-3 py-1" onClick={() => void loadJobs()} variant="ghost">
          Refresh
        </Button>
      </div>
      <div className="mt-3 space-y-2">
        {jobs.map((job) => (
          <div
            className="flex items-center justify-between gap-3 rounded-lg bg-surface2 px-3 py-2 text-xs text-on-surface-muted"
            key={job.job_id}
          >
            <span>{job.job_type}</span>
            <span>{job.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
