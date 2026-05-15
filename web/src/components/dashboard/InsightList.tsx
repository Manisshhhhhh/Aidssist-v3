import type { Insight, InsightSeverity } from "../../types/analysis";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

type InsightListProps = {
  insights: Insight[];
};

export function InsightList({ insights }: InsightListProps) {
  return (
    <Card>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Key insights
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Signals from the profile</h2>
      </div>

      {insights.length === 0 ? (
        <p className="mt-5 rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
          No deterministic insights were generated for this dataset.
        </p>
      ) : (
        <div className="mt-5 space-y-3">
          {insights.map((insight, index) => (
            <article
              className={`rounded-xl border p-4 ${getSeverityClasses(insight.severity)}`}
              key={`${insight.type}-${insight.title}-${index}`}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="font-semibold text-on-surface">{insight.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-on-surface">{insight.message}</p>
                </div>
                <Badge className="shrink-0">{insight.severity}</Badge>
              </div>

              {insight.columns.length > 0 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {insight.columns.map((column) => (
                    <span
                      className="rounded-full border border-outline bg-surface2 px-2.5 py-1 text-xs text-on-surface-muted"
                      key={column}
                    >
                      {column}
                    </span>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}

function getSeverityClasses(severity: InsightSeverity): string {
  const classes: Record<InsightSeverity, string> = {
    high: "border-danger/25 bg-danger/10",
    medium: "border-warning/25 bg-warning/10",
    low: "border-primary/20 bg-primary/10",
    info: "border-outline bg-surface1",
  };

  return classes[severity];
}
