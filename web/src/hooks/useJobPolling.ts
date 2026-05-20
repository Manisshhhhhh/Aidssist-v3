import { useEffect, useState } from "react";

import { getFriendlyApiErrorMessage } from "../api/errors";
import { getJob } from "../api/jobs";
import type { JobResponse } from "../types/jobs";

const terminalStatuses = new Set(["succeeded", "failed", "cancelled"]);

export function useJobPolling(jobId: string | null, intervalMs = 2000) {
  const [job, setJob] = useState<JobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      setError(null);
      setIsPolling(false);
      return;
    }

    let cancelled = false;
    let timeoutId: number | null = null;
    const activeJobId = jobId;

    async function poll() {
      setIsPolling(true);
      try {
        const nextJob = await getJob(activeJobId);
        if (cancelled) return;
        setJob(nextJob);
        setError(null);
        if (!terminalStatuses.has(nextJob.status)) {
          timeoutId = window.setTimeout(poll, intervalMs);
        } else {
          setIsPolling(false);
        }
      } catch (pollError) {
        if (cancelled) return;
        setError(getFriendlyApiErrorMessage(pollError, { fallback: "Unable to load job status." }));
        setIsPolling(false);
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [intervalMs, jobId]);

  return { job, error, isPolling };
}
