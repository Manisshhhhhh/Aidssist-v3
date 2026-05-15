import { useState } from "react";
import { motion } from "framer-motion";

import type { RecommendedChart } from "../../types/analysis";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { ChartCard } from "./ChartCard";

type ChartsPanelProps = {
  datasetId: string;
  charts: RecommendedChart[];
};

const INITIAL_CHART_COUNT = 6;

export function ChartsPanel({ datasetId, charts }: ChartsPanelProps) {
  const [visibleCount, setVisibleCount] = useState(INITIAL_CHART_COUNT);
  const visibleCharts = charts.slice(0, visibleCount);
  const remainingCount = Math.max(0, charts.length - visibleCount);

  if (charts.length === 0) {
    return (
      <Card>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Visualizations
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Interactive charts</h2>
        <p className="mt-5 rounded-xl border border-outline bg-surface1 p-4 text-sm text-on-surface-muted">
          No recommended charts are available for this dataset.
        </p>
      </Card>
    );
  }

  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.36, ease: "easeOut" }}
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Visualizations
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-on-surface">Interactive chart views</h2>
        <p className="mt-2 text-sm leading-6 text-on-surface-muted">
          Rendered from backend chart-data endpoints using the stored dataset and chart specs.
        </p>
      </div>

      <motion.div className="grid gap-5 xl:grid-cols-2" layout>
        {visibleCharts.map((chart, index) => (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            initial={{ opacity: 0, y: 12 }}
            key={chart.chart_id}
            layout
            transition={{ delay: Math.min(index * 0.035, 0.18), duration: 0.3, ease: "easeOut" }}
          >
            <ChartCard chart={chart} datasetId={datasetId} />
          </motion.div>
        ))}
      </motion.div>

      {remainingCount > 0 ? (
        <div className="flex justify-center">
          <Button
            onClick={() => setVisibleCount((current) => current + INITIAL_CHART_COUNT)}
            variant="secondary"
          >
            Load more charts ({remainingCount} remaining)
          </Button>
        </div>
      ) : null}
    </motion.section>
  );
}
