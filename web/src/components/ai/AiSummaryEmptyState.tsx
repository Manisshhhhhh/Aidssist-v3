import { Sparkles } from "lucide-react";

export function AiSummaryEmptyState() {
  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
        <Sparkles size={18} aria-hidden="true" />
      </div>
      <p className="font-semibold text-on-surface">Optional AI explanation</p>
      <p className="mt-2 leading-6">
        Generate a concise summary after deterministic analysis is available. No raw CSV rows are
        sent by this panel.
      </p>
    </div>
  );
}
