import { Activity, CalendarDays, Gauge, Ruler, Sigma, Target } from "lucide-react";

import type { ForecastResponse } from "../../types/forecast";
import { Card } from "../ui/Card";

type ForecastMetricsProps = {
  forecast: ForecastResponse;
};

export function ForecastMetrics({ forecast }: ForecastMetricsProps) {
  const metrics = [
    { label: "Model", value: formatModelName(forecast.model_used), icon: Activity },
    { label: "Frequency", value: formatFrequency(forecast.frequency), icon: CalendarDays },
    { label: "Horizon", value: `${forecast.periods} periods`, icon: Target },
    {
      label: "History",
      value: `${forecast.historical_points.length.toLocaleString()} points`,
      icon: Ruler,
    },
    { label: "MAE", value: formatMetric(forecast.metrics.mae), icon: Gauge },
    { label: "RMSE", value: formatMetric(forecast.metrics.rmse), icon: Sigma },
    { label: "MAPE", value: formatMetric(forecast.metrics.mape, "%"), icon: Gauge },
  ];

  return (
    <Card>
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
        Forecast metrics
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <div
              className="rounded-xl border border-outline bg-surface1 p-4 transition hover:bg-surface3"
              key={metric.label}
            >
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-primary/25 bg-primary/10 text-primary-light">
                <Icon size={17} aria-hidden="true" />
              </div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-muted">
                {metric.label}
              </p>
              <p className="mt-2 text-sm font-semibold text-on-surface">{metric.value}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function formatMetric(value: number | null, suffix = ""): string {
  if (value === null) {
    return "Not enough data";
  }

  const formatted = Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  return `${formatted}${suffix}`;
}

function formatFrequency(frequency: string): string {
  const labels: Record<string, string> = {
    D: "Daily",
    W: "Weekly",
    M: "Monthly",
    auto: "Auto",
  };

  return labels[frequency] ?? frequency;
}

function formatModelName(model: string): string {
  return model
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
