import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Loader2, Maximize2, RefreshCw } from "lucide-react";

import { getChartData } from "../../api/charts";
import type { RecommendedChart } from "../../types/analysis";
import type { ChartDataResponse, ChartTimeRange } from "../../types/charts";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ChartFullscreenModal } from "./ChartFullscreenModal";
import { ChartRenderer } from "./ChartRenderer";
import { ChartTimeRangeControl } from "./ChartTimeRangeControl";
import { EmptyChartState } from "./EmptyChartState";

type ChartCardProps = {
  datasetId: string;
  chart: RecommendedChart;
};

export function ChartCard({ datasetId, chart }: ChartCardProps) {
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);
  const [timeRange, setTimeRange] = useState<ChartTimeRange>("all");
  const [error, setError] = useState<string | null>(null);
  const supportsTimeRange = chart.chart_type === "line" || chart.chart_type === "area";

  const loadChart = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setChartData(await getChartData(datasetId, chart.chart_id, supportsTimeRange ? timeRange : "all"));
    } catch (chartError) {
      setError(chartError instanceof Error ? chartError.message : "Unable to load chart data.");
    } finally {
      setIsLoading(false);
    }
  }, [chart.chart_id, datasetId, supportsTimeRange, timeRange]);

  useEffect(() => {
    void loadChart();
  }, [loadChart]);

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="h-full"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.32, ease: "easeOut" }}
    >
      <Card className="h-full">
        <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="tracking-normal">{chart.chart_type}</Badge>
              <span className="rounded-full border border-outline bg-surface1 px-2.5 py-1 text-xs text-on-surface-muted">
                Priority {chart.priority}
              </span>
            </div>
            <h3 className="mt-3 text-lg font-semibold text-on-surface">{chart.title}</h3>
            <p className="mt-2 text-sm leading-6 text-on-surface-muted">{chart.reason}</p>
          </div>

          <div className="flex shrink-0 gap-2">
            <Button
              aria-label={`Open ${chart.title} full size`}
              className="min-h-10 px-3"
              onClick={() => setIsFullscreenOpen(true)}
              variant="secondary"
            >
              <Maximize2 size={16} aria-hidden="true" />
              Full size
            </Button>
            <Button
              aria-label={`Reload ${chart.title}`}
              className="min-h-10 px-3"
              disabled={isLoading}
              onClick={() => void loadChart()}
              variant="ghost"
            >
              <RefreshCw className={isLoading ? "animate-spin" : ""} size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>

        {supportsTimeRange ? (
          <div className="mb-4">
            <ChartTimeRangeControl
              disabled={isLoading}
              onChange={setTimeRange}
              value={timeRange}
            />
          </div>
        ) : null}

        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              animate={{ opacity: 1 }}
              className="shimmer flex h-72 items-center justify-center rounded-xl border border-outline bg-surface1 text-on-surface-muted"
              exit={{ opacity: 0 }}
              initial={{ opacity: 0 }}
              key="loading"
            >
              <Loader2 className="mr-2 animate-spin text-primary-light" size={18} aria-hidden="true" />
              Loading chart data
            </motion.div>
          ) : null}

          {!isLoading && error ? (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-danger"
              exit={{ opacity: 0, y: -8 }}
              initial={{ opacity: 0, y: 8 }}
              key="error"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 shrink-0" size={16} aria-hidden="true" />
                <p>{error}</p>
              </div>
            </motion.div>
          ) : null}

          {!isLoading && !error && chartData ? (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              initial={{ opacity: 0, y: 8 }}
              key="chart"
              transition={{ duration: 0.28, ease: "easeOut" }}
            >
              <ChartRenderer chartData={chartData} />
            </motion.div>
          ) : null}

          {!isLoading && !error && !chartData ? (
            <motion.div
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              initial={{ opacity: 0 }}
              key="empty"
            >
              <EmptyChartState />
            </motion.div>
          ) : null}
        </AnimatePresence>
      </Card>

      {isFullscreenOpen ? (
        <ChartFullscreenModal
          chart={chart}
          chartData={chartData}
          error={error}
          isLoading={isLoading}
          onClose={() => setIsFullscreenOpen(false)}
          onRefresh={loadChart}
          onTimeRangeChange={setTimeRange}
          supportsTimeRange={supportsTimeRange}
          timeRange={timeRange}
        />
      ) : null}
    </motion.div>
  );
}
