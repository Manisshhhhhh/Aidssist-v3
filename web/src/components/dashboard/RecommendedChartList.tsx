import { BarChart3 } from "lucide-react";

import type { RecommendedChart } from "../../types/analysis";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

type RecommendedChartListProps = {
  charts: RecommendedChart[];
};

export function RecommendedChartList({ charts }: RecommendedChartListProps) {
  return (
    <Card>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Recommended charts
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Visualization specs</h2>
      </div>

      {charts.length === 0 ? (
        <p className="mt-5 rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
          No chart recommendations were generated for this dataset.
        </p>
      ) : (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {charts.map((chart) => (
            <article
              className="rounded-xl border border-outline bg-surface1 p-4 transition hover:bg-surface3"
              key={chart.chart_id}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
                    <BarChart3 size={18} aria-hidden="true" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-on-surface">{chart.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-on-surface-muted">{chart.reason}</p>
                  </div>
                </div>
                <Badge className="shrink-0 tracking-normal">{chart.chart_type}</Badge>
              </div>

              <div className="mt-4 grid gap-2 text-xs text-on-surface-muted sm:grid-cols-3">
                <Spec label="X" value={chart.x} />
                <Spec label="Y" value={chart.y ?? "none"} />
                <Spec label="Priority" value={String(chart.priority)} />
              </div>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface2 px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.12em] text-on-surface-disabled">{label}</p>
      <p className="mt-1 truncate text-on-surface">{value}</p>
    </div>
  );
}
