import { ExternalLink, FileCheck2 } from "lucide-react";
import { useState } from "react";

import { getFriendlyApiErrorMessage } from "../../api/errors";
import { downloadReport } from "../../api/report";
import type { ReportResponse } from "../../types/report";
import { Button } from "../ui/Button";

type ReportResultProps = {
  report: ReportResponse;
};

export function ReportResult({ report }: ReportResultProps) {
  const [error, setError] = useState<string | null>(null);

  async function handleOpenReport() {
    setError(null);
    try {
      const blob = await downloadReport(report.dataset_id, report.report_id);
      const objectUrl = URL.createObjectURL(blob);
      window.open(objectUrl, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (downloadError) {
      setError(getFriendlyApiErrorMessage(downloadError, { fallback: "Unable to open report." }));
    }
  }

  return (
    <div className="rounded-xl border border-success/25 bg-success/10 p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <FileCheck2 className="mt-1 shrink-0 text-success" size={20} aria-hidden="true" />
          <div>
            <p className="font-semibold text-on-surface">Report generated</p>
            <p className="mt-1 break-all text-sm text-on-surface-muted">{report.filename}</p>
            <p className="mt-1 text-xs text-on-surface-disabled">
              {new Date(report.created_at).toLocaleString()}
            </p>
          </div>
        </div>

        <Button onClick={() => void handleOpenReport()} variant="secondary">
          <ExternalLink size={17} aria-hidden="true" />
          Open report
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
    </div>
  );
}
