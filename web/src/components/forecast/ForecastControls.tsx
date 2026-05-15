import { useEffect, useState } from "react";
import { Loader2, WandSparkles } from "lucide-react";

import type { ColumnProfile } from "../../types/analysis";
import type { ForecastFrequency, ForecastModel, ForecastRequest } from "../../types/forecast";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type ForecastControlsProps = {
  datetimeColumns: ColumnProfile[];
  numericColumns: ColumnProfile[];
  isLoading: boolean;
  onSubmit: (request: ForecastRequest) => void;
};

const frequencyOptions: Array<{ label: string; value: ForecastFrequency }> = [
  { label: "Auto", value: "auto" },
  { label: "Daily", value: "D" },
  { label: "Weekly", value: "W" },
  { label: "Monthly", value: "M" },
];

const modelOptions: Array<{ label: string; value: ForecastModel }> = [
  { label: "Auto", value: "auto" },
  { label: "Linear regression", value: "linear_regression" },
  { label: "Moving average", value: "moving_average" },
];

export function ForecastControls({
  datetimeColumns,
  numericColumns,
  isLoading,
  onSubmit,
}: ForecastControlsProps) {
  const [dateColumn, setDateColumn] = useState(datetimeColumns[0]?.name ?? "");
  const [targetColumn, setTargetColumn] = useState(numericColumns[0]?.name ?? "");
  const [periods, setPeriods] = useState("12");
  const [frequency, setFrequency] = useState<ForecastFrequency>("auto");
  const [model, setModel] = useState<ForecastModel>("auto");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDateColumn(datetimeColumns[0]?.name ?? "");
    setTargetColumn(numericColumns[0]?.name ?? "");
  }, [datetimeColumns, numericColumns]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const parsedPeriods = Number(periods);
    const validationError = validateForecastRequest(dateColumn, targetColumn, parsedPeriods);

    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    onSubmit({
      date_column: dateColumn,
      target_column: targetColumn,
      periods: parsedPeriods,
      frequency,
      model,
    });
  }

  return (
    <Card>
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Forecast setup
          </p>
          <h3 className="mt-2 text-xl font-semibold text-on-surface">
            Generate a statistical projection
          </h3>
          <p className="mt-2 text-sm leading-6 text-on-surface-muted">
            Select a datetime axis and numeric target. Aidssist will call the deterministic
            backend forecasting engine and return assumptions with the result.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Field label="Date column">
            <select
              className={inputClasses}
              onChange={(event) => setDateColumn(event.target.value)}
              value={dateColumn}
            >
              {datetimeColumns.map((column) => (
                <option key={column.name} value={column.name}>
                  {column.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Target column">
            <select
              className={inputClasses}
              onChange={(event) => setTargetColumn(event.target.value)}
              value={targetColumn}
            >
              {numericColumns.map((column) => (
                <option key={column.name} value={column.name}>
                  {column.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Periods">
            <input
              className={inputClasses}
              max={60}
              min={1}
              onChange={(event) => setPeriods(event.target.value)}
              step={1}
              type="number"
              value={periods}
            />
          </Field>

          <Field label="Frequency">
            <select
              className={inputClasses}
              onChange={(event) => setFrequency(event.target.value as ForecastFrequency)}
              value={frequency}
            >
              {frequencyOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Model">
            <select
              className={inputClasses}
              onChange={(event) => setModel(event.target.value as ForecastModel)}
              value={model}
            >
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
        </div>

        {error ? (
          <p className="animate-reveal-up rounded-xl border border-danger/25 bg-danger/10 px-4 py-3 text-sm text-danger">
            {error}
          </p>
        ) : null}

        <div className="flex flex-wrap items-center gap-3">
          <Button disabled={isLoading} type="submit">
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={18} aria-hidden="true" />
                Running forecast
              </>
            ) : (
              <>
                <WandSparkles size={18} aria-hidden="true" />
                Run forecast
              </>
            )}
          </Button>
          <p className="text-xs leading-5 text-on-surface-muted">
            Forecasts are estimates, not certainty. External events are not modeled.
          </p>
        </div>
      </form>
    </Card>
  );
}

function Field({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-muted">
        {label}
      </span>
      {children}
    </label>
  );
}

function validateForecastRequest(
  dateColumn: string,
  targetColumn: string,
  periods: number,
): string | null {
  if (!dateColumn) {
    return "Choose a datetime column.";
  }

  if (!targetColumn) {
    return "Choose a numeric target column.";
  }

  if (dateColumn === targetColumn) {
    return "Date and target columns must be different.";
  }

  if (!Number.isInteger(periods) || periods < 1 || periods > 60) {
    return "Periods must be a whole number between 1 and 60.";
  }

  return null;
}

const inputClasses =
  "min-h-11 w-full rounded-xl border border-outline bg-surface1 px-3 py-2 text-sm text-on-surface outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20";
