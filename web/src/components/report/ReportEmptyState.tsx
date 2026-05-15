import { FileWarning } from "lucide-react";

export function ReportEmptyState() {
  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4">
      <div className="flex items-start gap-3">
        <FileWarning className="mt-0.5 shrink-0 text-warning" size={18} aria-hidden="true" />
        <div>
          <p className="font-semibold text-on-surface">Report unavailable</p>
          <p className="mt-1 text-sm leading-6 text-on-surface-muted">
            Run dataset analysis before generating an exportable report.
          </p>
        </div>
      </div>
    </div>
  );
}
