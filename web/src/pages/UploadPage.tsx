import { lazy, Suspense, useState } from "react";
import { motion } from "framer-motion";
import { BarChart3, BrainCircuit, CheckCircle2, LineChart, MessageSquareText } from "lucide-react";

import { BrandMark } from "../components/brand/BrandMark";
import { DatasetList } from "../components/dashboard/DatasetList";
import { DataSourceConnectPanel } from "../components/upload/DataSourceConnectPanel";
import { FileUploadDropzone } from "../components/upload/FileUploadDropzone";
import { Badge } from "../components/ui/Badge";
import { Card } from "../components/ui/Card";
import { useWorkspace } from "../workspace/useWorkspace";
import type { DatasetMetadata } from "../types/dataset";

const DataGalaxy = lazy(() =>
  import("../components/three/DataGalaxy").then((module) => ({ default: module.DataGalaxy })),
);

const featureCards = [
  {
    title: "Analyze datasets",
    description: "Profile structure, quality, missing values, and statistical patterns.",
    icon: BarChart3,
  },
  {
    title: "Generate insights",
    description: "Surface deterministic signals from correlations, outliers, and quality checks.",
    icon: BrainCircuit,
  },
  {
    title: "Forecast future trends",
    description: "Run statistical forecasts with assumptions, warnings, and confidence bands.",
    icon: LineChart,
  },
  {
    title: "Ask your data",
    description: "Prepare for conversational exploration once the backend query layer arrives.",
    icon: MessageSquareText,
  },
];

type UploadPageProps = {
  onOpenDashboard: (datasetId: string) => void;
};

export function UploadPage({ onOpenDashboard }: UploadPageProps) {
  const [uploadedDataset, setUploadedDataset] = useState<DatasetMetadata | null>(null);
  const [refreshSignal, setRefreshSignal] = useState(0);
  const { selectedWorkspace, selectedWorkspaceId } = useWorkspace();

  function handleUploadSuccess(dataset: DatasetMetadata) {
    setUploadedDataset(dataset);
    setRefreshSignal((current) => current + 1);
    onOpenDashboard(dataset.dataset_id);
  }

  return (
    <div className="w-full space-y-10">
      <motion.section
        animate={{ opacity: 1, y: 0 }}
        className="relative mx-auto max-w-4xl overflow-hidden rounded-[2rem] px-4 py-12 text-center sm:px-8"
        initial={{ opacity: 0, y: 18 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <Suspense fallback={null}>
          <DataGalaxy className="opacity-55 mix-blend-screen" />
        </Suspense>
        <div className="relative z-10">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-primary/25 bg-surface1/80 text-primary-light shadow-panel backdrop-blur">
            <BrandMark size={42} variant="duo" />
          </div>
          <Badge>V3 Intelligence Core</Badge>
          <h1 className="mx-auto mt-6 max-w-4xl text-4xl font-semibold leading-tight text-on-surface sm:text-5xl lg:text-6xl">
            Upload data into the Aidssist intelligence pipeline.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-on-surface-muted sm:text-lg">
            Upload a dataset, validate its shape, generate deterministic insights, and prepare
            forecasting workflows from one focused workspace.
          </p>
        </div>
      </motion.section>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          initial={{ opacity: 0, y: 18 }}
          transition={{ delay: 0.08, duration: 0.45 }}
        >
          <FileUploadDropzone
            onUploadSuccess={handleUploadSuccess}
            workspaceId={selectedWorkspaceId}
          />

          {uploadedDataset ? (
            <Card className="mt-5 border-success/25 bg-success/10">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-1 shrink-0 text-success" size={20} aria-hidden="true" />
                <div>
                  <p className="font-semibold text-on-surface">Dataset registered</p>
                  <p className="mt-2 text-sm leading-6 text-on-surface">
                  {uploadedDataset.original_filename} is ready for the next dashboard step with{" "}
                  {formatNullableNumber(uploadedDataset.row_count)} rows and{" "}
                    {formatNullableNumber(uploadedDataset.column_count)} columns
                    {selectedWorkspace ? ` in ${selectedWorkspace.name}.` : "."}
                  </p>
                </div>
              </div>
            </Card>
          ) : null}
        </motion.div>

        <motion.div
          animate={{ opacity: 1, y: 0 }}
          initial={{ opacity: 0, y: 18 }}
          transition={{ delay: 0.14, duration: 0.45 }}
        >
          <DatasetList
            onDatasetSelect={(dataset) => onOpenDashboard(dataset.dataset_id)}
            refreshSignal={refreshSignal}
            workspaceId={selectedWorkspaceId}
          />
        </motion.div>
      </div>

      <motion.div
        animate={{ opacity: 1, y: 0 }}
        initial={{ opacity: 0, y: 18 }}
        transition={{ delay: 0.18, duration: 0.45 }}
      >
        <DataSourceConnectPanel />
      </motion.div>

      <motion.div
        animate={{ opacity: 1, scale: 1 }}
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        initial={{ opacity: 0, scale: 0.98 }}
        transition={{ delay: 0.2, duration: 0.55, ease: "easeOut" }}
      >
        {featureCards.map((feature, index) => {
          const Icon = feature.icon;

          return (
            <motion.div
              animate={{ opacity: 1, y: 0 }}
              initial={{ opacity: 0, y: 16 }}
              key={feature.title}
              transition={{ delay: 0.16 + index * 0.06, duration: 0.4 }}
            >
              <Card className="h-full">
                <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
                  <Icon size={21} aria-hidden="true" />
                </div>
                <h2 className="text-lg font-semibold text-on-surface">{feature.title}</h2>
                <p className="mt-3 text-sm leading-6 text-on-surface-muted">{feature.description}</p>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}

function formatNullableNumber(value: number | null | undefined): string {
  return typeof value === "number" ? value.toLocaleString() : "unknown";
}
