import { TrendingDown, TrendingUp } from "lucide-react";

import type { Correlation } from "../../types/analysis";
import { Card } from "../ui/Card";

type CorrelationPanelProps = {
  correlations: Correlation[];
};

export function CorrelationPanel({ correlations }: CorrelationPanelProps) {
  return (
    <Card>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Correlations
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Strong numeric relationships</h2>
      </div>

      {correlations.length === 0 ? (
        <p className="mt-5 rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
          No numeric correlations above the backend threshold were detected.
        </p>
      ) : (
        <div className="mt-5 space-y-3">
          {correlations.map((correlation) => {
            const isPositive = correlation.correlation >= 0;
            const Icon = isPositive ? TrendingUp : TrendingDown;

            return (
              <div
                className="rounded-xl border border-outline bg-surface1 p-4 transition hover:bg-surface3"
                key={`${correlation.column_a}-${correlation.column_b}`}
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate font-semibold text-on-surface">
                      {correlation.column_a} ↔ {correlation.column_b}
                    </p>
                    <p className="mt-1 text-sm text-on-surface-muted">
                      {isPositive ? "Positive" : "Negative"} relationship
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-primary-light">
                    <Icon size={18} aria-hidden="true" />
                    <span className="font-mono text-lg font-semibold">
                      {correlation.correlation.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
