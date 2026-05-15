import { TrendingUp } from "lucide-react";

import { Card } from "../ui/Card";

type ForecastEmptyStateProps = {
  message?: string;
};

export function ForecastEmptyState({
  message = "Forecasting requires at least one datetime column and one numeric column.",
}: ForecastEmptyStateProps) {
  return (
    <Card>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="soft-icon flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
          <TrendingUp size={22} aria-hidden="true" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Forecasting
          </p>
          <h2 className="mt-2 text-xl font-semibold text-on-surface">Forecast unavailable</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-on-surface-muted">{message}</p>
        </div>
      </div>
    </Card>
  );
}
