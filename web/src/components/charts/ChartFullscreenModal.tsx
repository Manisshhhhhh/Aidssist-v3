import { useEffect, useState } from "react";
import { Activity, Loader2, RefreshCw, X } from "lucide-react";

import type { RecommendedChart } from "../../types/analysis";
import type { ChartDataResponse, ChartTimeRange } from "../../types/charts";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ChartRenderer } from "./ChartRenderer";
import { ChartTimeRangeControl } from "./ChartTimeRangeControl";
import { EmptyChartState } from "./EmptyChartState";

type ChartFullscreenModalProps = {
  chart: RecommendedChart;
  chartData: ChartDataResponse | null;
  error: string | null;
  isLoading: boolean;
  onClose: () => void;
  onRefresh: () => Promise<void>;
  onTimeRangeChange: (value: ChartTimeRange) => void;
  supportsTimeRange: boolean;
  timeRange: ChartTimeRange;
};

const MONITOR_INTERVAL_MS = 30000;

export function ChartFullscreenModal({
  chart,
  chartData,
  error,
  isLoading,
  onClose,
  onRefresh,
  onTimeRangeChange,
  supportsTimeRange,
  timeRange,
}: ChartFullscreenModalProps) {
  const [isMonitoring, setIsMonitoring] = useState(false);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!isMonitoring) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void onRefresh();
    }, MONITOR_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [isMonitoring, onRefresh]);

  return (
    <div
      aria-label={`${chart.title} full-size chart viewer`}
      aria-modal="true"
      className="fixed inset-0 z-50 flex bg-background/92 p-3 backdrop-blur-xl sm:p-6"
      role="dialog"
    >
      <div className="flex min-h-0 w-full flex-col overflow-hidden rounded-2xl border border-outline bg-surface2 shadow-panel">
        <header className="flex flex-col gap-4 border-b border-outline bg-surface1 px-4 py-4 sm:flex-row sm:items-start sm:justify-between sm:px-6">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="tracking-normal">{chart.chart_type}</Badge>
              <span className="rounded-full border border-outline bg-surface2 px-2.5 py-1 text-xs text-on-surface-muted">
                Priority {chart.priority}
              </span>
              {isMonitoring ? (
                <span className="inline-flex items-center gap-1 rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-xs text-success">
                  <Activity size={13} aria-hidden="true" />
                  Monitoring
                </span>
              ) : null}
            </div>
            <h2 className="mt-3 truncate text-xl font-semibold text-on-surface sm:text-2xl">
              {chart.title}
            </h2>
            <p className="mt-1 line-clamp-2 text-sm text-on-surface-muted">{chart.reason}</p>
            {chartData ? (
              <p className="mt-2 text-xs text-on-surface-disabled">
                Last refreshed {new Date(chartData.created_at).toLocaleString()}
              </p>
            ) : null}
          </div>

          <div className="flex shrink-0 flex-wrap gap-2">
            <Button
              className="min-h-10 px-3"
              disabled={isLoading}
              onClick={() => void onRefresh()}
              variant="secondary"
            >
              <RefreshCw className={isLoading ? "animate-spin" : ""} size={16} aria-hidden="true" />
              Refresh
            </Button>
            <Button
              className="min-h-10 px-3"
              onClick={() => setIsMonitoring((current) => !current)}
              variant={isMonitoring ? "primary" : "secondary"}
            >
              <Activity size={16} aria-hidden="true" />
              {isMonitoring ? "Stop monitor" : "Monitor"}
            </Button>
            <Button aria-label="Close full-size chart" className="min-h-10 px-3" onClick={onClose} variant="ghost">
              <X size={18} aria-hidden="true" />
            </Button>
          </div>
        </header>

        {supportsTimeRange ? (
          <div className="border-b border-outline bg-surface2 px-4 py-3 sm:px-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-muted">
                Time period
              </p>
              <ChartTimeRangeControl
                disabled={isLoading}
                onChange={onTimeRangeChange}
                value={timeRange}
              />
            </div>
          </div>
        ) : null}

        <main className="min-h-0 flex-1 overflow-auto p-4 sm:p-6">
          {isLoading ? (
            <div className="shimmer flex h-[62vh] min-h-[420px] items-center justify-center rounded-xl border border-outline bg-surface1 text-on-surface-muted">
              <Loader2 className="mr-2 animate-spin text-primary-light" size={18} aria-hidden="true" />
              Loading full-size chart
            </div>
          ) : null}

          {!isLoading && error ? (
            <div className="rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-danger">
              {error}
            </div>
          ) : null}

          {!isLoading && !error && chartData ? (
            <ChartRenderer chartData={chartData} size="full" />
          ) : null}

          {!isLoading && !error && !chartData ? <EmptyChartState /> : null}
        </main>
      </div>
    </div>
  );
}
