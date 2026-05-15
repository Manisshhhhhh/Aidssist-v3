import { useState } from "react";
import { AlertCircle, FileText, Loader2 } from "lucide-react";

import { createReport, createReportJob } from "../../api/report";
import type { AnalysisResponse } from "../../types/analysis";
import type { JobResponse } from "../../types/jobs";
import type { ReportRequest, ReportResponse } from "../../types/report";
import { useJobPolling } from "../../hooks/useJobPolling";
import { useWorkspace } from "../../workspace/useWorkspace";
import { JobHistoryPanel } from "../jobs/JobHistoryPanel";
import { JobStatusCard } from "../jobs/JobStatusCard";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ReportEmptyState } from "./ReportEmptyState";
import { ReportOptions } from "./ReportOptions";
import { ReportResult } from "./ReportResult";

type ReportPanelProps = {
  analysis?: AnalysisResponse | null;
  datasetId: string;
};

const defaultOptions: ReportRequest = {
  format: "html",
  include_forecast: true,
  include_charts: true,
  include_chat_summary: false,
  include_ai_summary: false,
};

export function ReportPanel({ analysis, datasetId }: ReportPanelProps) {
  const [options, setOptions] = useState<ReportRequest>(defaultOptions);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [generateInBackground, setGenerateInBackground] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { selectedWorkspaceId } = useWorkspace();
  const { error: jobError, job } = useJobPolling(jobId);

  async function handleGenerateReport() {
    if (!analysis || isGenerating) {
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      setJobId(null);
      if (generateInBackground) {
        const createdJob = await createReportJob(datasetId, options);
        setJobId(createdJob.job_id);
        return;
      }
      setReport(await createReport(datasetId, options));
    } catch (reportError) {
      setError(reportError instanceof Error ? reportError.message : "Unable to generate report.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <Card>
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Export report
          </p>
          <h2 className="mt-2 text-xl font-semibold text-on-surface">Analysis deliverable</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-on-surface-muted">
            Generate a self-contained report grounded in metadata, analysis, insights, chart
            recommendations, and the latest saved forecast when available.
          </p>
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
          <FileText size={20} aria-hidden="true" />
        </div>
      </div>

      {!analysis ? <ReportEmptyState /> : null}

      {analysis ? (
        <div className="space-y-5">
          <ReportOptions disabled={isGenerating} onChange={setOptions} value={options} />

          <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface">
            <span>
              <span className="block font-semibold">Generate in background</span>
              <span className="mt-1 block text-xs text-on-surface-muted">
                Enqueue this report and poll job status while you keep working.
              </span>
            </span>
            <input
              checked={generateInBackground}
              className="h-4 w-4 accent-primary"
              disabled={isGenerating}
              onChange={(event) => setGenerateInBackground(event.target.checked)}
              type="checkbox"
            />
          </label>

          {error ? (
            <div className="flex items-start gap-3 rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-on-surface">
              <AlertCircle className="mt-0.5 shrink-0 text-danger" size={18} aria-hidden="true" />
              <p>{error}</p>
            </div>
          ) : null}

          {jobId ? (
            <JobStatusCard error={jobError} job={job} title="Report generation job" />
          ) : null}

          {job?.status === "succeeded" && isReportResponse(job.output) ? (
            <ReportResult report={job.output} />
          ) : report ? (
            <ReportResult report={report} />
          ) : null}

          <JobHistoryPanel workspaceId={selectedWorkspaceId} />

          <Button disabled={isGenerating} onClick={() => void handleGenerateReport()}>
            {isGenerating ? <Loader2 className="animate-spin" size={18} aria-hidden="true" /> : null}
            Generate report
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

function isReportResponse(output: JobResponse["output"]): output is ReportResponse {
  if (!output || typeof output !== "object") {
    return false;
  }
  const candidate = output as Record<string, unknown>;
  return Boolean(
    typeof candidate.dataset_id === "string" &&
      typeof candidate.report_id === "string" &&
      (candidate.format === "html" || candidate.format === "json") &&
      typeof candidate.filename === "string" &&
      typeof candidate.download_url === "string" &&
      typeof candidate.created_at === "string",
  );
}
