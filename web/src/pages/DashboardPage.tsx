import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { motion, type Variants } from "framer-motion";
import { AlertCircle, ArrowLeft, Loader2, RefreshCw } from "lucide-react";

import { analyzeDataset } from "../api/analysis";
import { getFriendlyApiErrorMessage } from "../api/errors";
import { AiSummaryPanel } from "../components/ai/AiSummaryPanel";
import { BrandMark } from "../components/brand/BrandMark";
import { ChartsPanel } from "../components/charts/ChartsPanel";
import { AskDataPanel } from "../components/chat/AskDataPanel";
import { ColumnProfileTable } from "../components/dashboard/ColumnProfileTable";
import { CorrelationPanel } from "../components/dashboard/CorrelationPanel";
import { DataQualityPanel } from "../components/dashboard/DataQualityPanel";
import { DatasetOverviewCards } from "../components/dashboard/DatasetOverviewCards";
import { InsightList } from "../components/dashboard/InsightList";
import { RecommendedChartList } from "../components/dashboard/RecommendedChartList";
import { ForecastPanel } from "../components/forecast/ForecastPanel";
import { ReportPanel } from "../components/report/ReportPanel";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import type { AnalysisResponse } from "../types/analysis";

const DataGalaxy = lazy(() =>
  import("../components/three/DataGalaxy").then((module) => ({ default: module.DataGalaxy })),
);

type DashboardPageProps = {
  datasetId: string;
  onBack: () => void;
};

export function DashboardPage({ datasetId, onBack }: DashboardPageProps) {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setAnalysis(await analyzeDataset(datasetId));
    } catch (analysisError) {
      setError(getAnalysisErrorMessage(analysisError));
    } finally {
      setIsLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    void loadAnalysis();
  }, [loadAnalysis]);

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="w-full space-y-6"
      initial={{ opacity: 0, y: 18 }}
      transition={{ duration: 0.45, ease: "easeOut" }}
    >
      <div className="relative overflow-hidden rounded-[1.75rem] border border-outline bg-surface1/70 p-5 shadow-panel backdrop-blur sm:p-6">
        <Suspense fallback={null}>
          <DataGalaxy className="opacity-35 mix-blend-screen" compact />
        </Suspense>
        <div className="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <Button onClick={onBack} variant="ghost" className="mb-4 px-0 hover:bg-transparent">
              <ArrowLeft size={18} aria-hidden="true" />
              Back to uploads
            </Button>
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-primary/25 bg-primary/10 text-primary-light">
              <BrandMark size={34} variant="duo" />
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
              Analysis dashboard
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-on-surface sm:text-4xl">
              Dataset intelligence profile
            </h1>
            <p className="mt-3 break-all font-mono text-xs text-on-surface-muted">{datasetId}</p>
          </div>

          <Button onClick={() => void loadAnalysis()} disabled={isLoading} variant="secondary">
            <RefreshCw className={isLoading ? "animate-spin" : ""} size={18} aria-hidden="true" />
            Retry analysis
          </Button>
        </div>
      </div>

      {isLoading ? <AnalysisLoading /> : null}

      {!isLoading && error ? (
        <Card className="border-danger/25 bg-danger/10">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-1 shrink-0 text-danger" size={20} aria-hidden="true" />
            <div>
              <h2 className="font-semibold text-on-surface">Analysis failed</h2>
              <p className="mt-2 text-sm leading-6 text-on-surface">{error}</p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Button onClick={() => void loadAnalysis()} variant="secondary">
                  Retry
                </Button>
                <Button onClick={onBack} variant="ghost">
                  Back
                </Button>
              </div>
            </div>
          </div>
        </Card>
      ) : null}

      {!isLoading && !error && analysis ? (
        <motion.div
          animate="show"
          className="space-y-6"
          initial="hidden"
          variants={dashboardSectionGroup}
        >
          <motion.div variants={dashboardSection}>
            <DatasetOverviewCards analysis={analysis} />
          </motion.div>
          <motion.div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]" variants={dashboardSection}>
            <DataQualityPanel quality={analysis.quality} />
            <InsightList insights={analysis.insights} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <AskDataPanel analysis={analysis} datasetId={datasetId} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <AiSummaryPanel analysis={analysis} datasetId={datasetId} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <ColumnProfileTable columns={analysis.columns} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <ChartsPanel charts={analysis.recommended_charts} datasetId={datasetId} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <ForecastPanel analysis={analysis} datasetId={datasetId} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <ReportPanel analysis={analysis} datasetId={datasetId} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <CorrelationPanel correlations={analysis.correlations} />
          </motion.div>
          <motion.div variants={dashboardSection}>
            <RecommendedChartList charts={analysis.recommended_charts} />
          </motion.div>
        </motion.div>
      ) : null}
    </motion.div>
  );
}

function AnalysisLoading() {
  return (
    <Card>
      <div className="flex items-center gap-3 text-on-surface">
        <Loader2 className="animate-spin text-primary-light" size={20} aria-hidden="true" />
        <div>
          <p className="font-semibold text-on-surface">Running deterministic analysis</p>
          <p className="mt-1 text-sm text-on-surface-muted">
            Profiling columns, quality, correlations, insights, and chart recommendations.
          </p>
        </div>
      </div>
    </Card>
  );
}

function getAnalysisErrorMessage(error: unknown): string {
  return getFriendlyApiErrorMessage(error, { fallback: "Unable to analyze this dataset." });
}

const dashboardSectionGroup: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const dashboardSection: Variants = {
  hidden: {
    opacity: 0,
    y: 18,
  },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.42,
      ease: "easeOut",
    },
  },
};
