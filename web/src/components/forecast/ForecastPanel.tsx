import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Loader2 } from "lucide-react";

import { createForecast } from "../../api/forecast";
import type { AnalysisResponse, ColumnProfile } from "../../types/analysis";
import type { ForecastRequest, ForecastResponse } from "../../types/forecast";
import { Card } from "../ui/Card";
import { ForecastChart } from "./ForecastChart";
import { ForecastControls } from "./ForecastControls";
import { ForecastEmptyState } from "./ForecastEmptyState";
import { ForecastMetrics } from "./ForecastMetrics";
import { ForecastWarnings } from "./ForecastWarnings";

type ForecastPanelProps = {
  analysis: AnalysisResponse;
  datasetId: string;
};

export function ForecastPanel({ analysis, datasetId }: ForecastPanelProps) {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [autoForecastAttempted, setAutoForecastAttempted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const autoForecastKeyRef = useRef<string | null>(null);

  const datetimeColumns = useMemo(
    () => analysis.columns.filter((column) => column.semantic_type === "datetime"),
    [analysis.columns],
  );
  const numericColumns = useMemo(
    () => analysis.columns.filter((column) => column.semantic_type === "numeric"),
    [analysis.columns],
  );
  const defaultForecastRequest = useMemo<ForecastRequest | null>(() => {
    const dateColumn = datetimeColumns[0]?.name;
    const targetColumn = numericColumns[0]?.name;

    if (!dateColumn || !targetColumn || dateColumn === targetColumn) {
      return null;
    }

    return {
      date_column: dateColumn,
      target_column: targetColumn,
      frequency: "auto",
      model: "auto",
      periods: 12,
    };
  }, [datetimeColumns, numericColumns]);

  async function handleCreateForecast(request: ForecastRequest) {
    setIsLoading(true);
    setError(null);

    try {
      setForecast(await createForecast(datasetId, request));
    } catch (forecastError) {
      setError(getForecastErrorMessage(forecastError));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (!defaultForecastRequest) {
      return;
    }

    const requestKey = [
      datasetId,
      defaultForecastRequest.date_column,
      defaultForecastRequest.target_column,
      defaultForecastRequest.periods,
      defaultForecastRequest.frequency,
      defaultForecastRequest.model,
    ].join(":");

    if (autoForecastKeyRef.current === requestKey) {
      return;
    }

    autoForecastKeyRef.current = requestKey;
    setAutoForecastAttempted(true);
    void handleCreateForecast(defaultForecastRequest);
  }, [datasetId, defaultForecastRequest]);

  if (datetimeColumns.length === 0 || numericColumns.length === 0) {
    return <ForecastEmptyState />;
  }

  const warnings = forecast ? withCollapsedBandWarning(forecast) : [];

  return (
    <section className="space-y-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Forecasting
        </p>
        <h2 className="mt-2 text-2xl font-semibold text-on-surface">Future trend projection</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-on-surface-muted">
          Aidssist automatically starts a deterministic forecast when valid datetime and numeric
          columns are available. You can adjust the setup and rerun the backend engine at any time.
        </p>
      </div>

      <ForecastControls
        datetimeColumns={datetimeColumns}
        isLoading={isLoading}
        numericColumns={numericColumns}
        onSubmit={(request) => void handleCreateForecast(request)}
      />

      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            initial={{ opacity: 0 }}
            key="loading"
          >
            <Card>
              <div className="flex items-center gap-3 text-on-surface">
                <Loader2 className="animate-spin text-primary-light" size={20} aria-hidden="true" />
                <div>
                  <p className="font-semibold text-on-surface">Forecast engine running</p>
                  <p className="mt-1 text-sm text-on-surface-muted">
                    Preparing time series, fitting the selected model, and estimating bands.
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        ) : null}

        {error ? (
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            initial={{ opacity: 0, y: 8 }}
            key="error"
          >
            <Card className="border-danger/25 bg-danger/10">
              <div className="flex items-start gap-3">
                <AlertCircle className="mt-1 shrink-0 text-danger" size={20} aria-hidden="true" />
                <div>
                  <h3 className="font-semibold text-on-surface">Forecast failed</h3>
                  <p className="mt-2 text-sm leading-6 text-on-surface">{error}</p>
                </div>
              </div>
            </Card>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {forecast ? (
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="space-y-5"
          initial={{ opacity: 0, y: 14 }}
          transition={{ duration: 0.38, ease: "easeOut" }}
        >
          <ForecastChart forecast={forecast} />
          <ForecastMetrics forecast={forecast} />
          <ForecastWarnings assumptions={forecast.assumptions} warnings={warnings} />
        </motion.div>
      ) : !isLoading ? (
        <ForecastReadyState
          autoForecastAttempted={autoForecastAttempted}
          datetimeColumns={datetimeColumns}
          numericColumns={numericColumns}
        />
      ) : null}
    </section>
  );
}

function ForecastReadyState({
  autoForecastAttempted,
  datetimeColumns,
  numericColumns,
}: {
  autoForecastAttempted: boolean;
  datetimeColumns: ColumnProfile[];
  numericColumns: ColumnProfile[];
}) {
  return (
    <Card>
      <p className="text-sm leading-6 text-on-surface-muted">
        {autoForecastAttempted
          ? "Automatic forecasting did not return a result yet. Review any warning above, adjust the setup, and run again."
          : `Ready to forecast with ${datetimeColumns.length} datetime column${
              datetimeColumns.length === 1 ? "" : "s"
            } and ${numericColumns.length} numeric target${
              numericColumns.length === 1 ? "" : "s"
            }. Automatic forecasting will start shortly.`}
      </p>
    </Card>
  );
}

function withCollapsedBandWarning(forecast: ForecastResponse): string[] {
  const hasCollapsedBand =
    forecast.forecast_points.length > 0 &&
    forecast.forecast_points.every(
      (point) =>
        point.lower_bound !== null &&
        point.upper_bound !== null &&
        Math.abs(point.lower_bound - point.predicted_value) < 1e-9 &&
        Math.abs(point.upper_bound - point.predicted_value) < 1e-9,
    );

  if (!hasCollapsedBand) {
    return forecast.warnings;
  }

  const warning = "Historical residual error is zero; confidence band may be unrealistically narrow.";
  return forecast.warnings.includes(warning) ? forecast.warnings : [...forecast.warnings, warning];
}

function getForecastErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to generate a forecast for this dataset.";
}
