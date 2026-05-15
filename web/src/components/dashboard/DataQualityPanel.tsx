import type { DataQuality } from "../../types/analysis";
import { Card } from "../ui/Card";

type DataQualityPanelProps = {
  quality: DataQuality;
};

export function DataQualityPanel({ quality }: DataQualityPanelProps) {
  const tone = getQualityTone(quality.quality_score);

  return (
    <Card>
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Data quality
          </p>
          <h2 className="mt-2 text-xl font-semibold text-on-surface">
            Quality score: {quality.quality_score}/100
          </h2>
          <p className="mt-2 text-sm leading-6 text-on-surface-muted">
            Deterministic score based on missingness, duplicates, empty columns, and
            constant columns.
          </p>
        </div>
        <div className={`rounded-lg border px-4 py-2 text-sm font-semibold ${tone.badge}`}>
          {tone.label}
        </div>
      </div>

      <div className="mt-6 h-3 overflow-hidden rounded-full bg-surface1">
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${tone.bar}`}
          style={{ width: `${Math.max(0, Math.min(100, quality.quality_score))}%` }}
        />
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <QualityMetric label="Missing cells" value={quality.missing_cells.toLocaleString()} />
        <QualityMetric label="Missing percent" value={`${quality.missing_percent}%`} />
        <QualityMetric label="Duplicate rows" value={quality.duplicate_rows.toLocaleString()} />
        <QualityMetric label="Duplicate percent" value={`${quality.duplicate_percent}%`} />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <ColumnList label="Empty columns" columns={quality.empty_columns} />
        <ColumnList label="Constant columns" columns={quality.constant_columns} />
      </div>
    </Card>
  );
}

function QualityMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4">
      <p className="text-xs uppercase tracking-[0.12em] text-on-surface-disabled">{label}</p>
      <p className="mt-2 text-lg font-semibold text-on-surface">{value}</p>
    </div>
  );
}

function ColumnList({ label, columns }: { label: string; columns: string[] }) {
  return (
    <div className="rounded-xl border border-outline bg-surface1 p-4">
      <p className="text-xs uppercase tracking-[0.12em] text-on-surface-disabled">{label}</p>
      <p className="mt-2 text-sm text-on-surface-muted">
        {columns.length > 0 ? columns.join(", ") : "None detected"}
      </p>
    </div>
  );
}

function getQualityTone(score: number) {
  if (score >= 90) {
    return {
      label: "High quality",
      badge: "border-success/25 bg-success/10 text-success",
      bar: "bg-success",
    };
  }

  if (score >= 70) {
    return {
      label: "Medium quality",
      badge: "border-warning/25 bg-warning/10 text-warning",
      bar: "bg-warning",
    };
  }

  return {
    label: "Low quality",
    badge: "border-danger/25 bg-danger/10 text-danger",
    bar: "bg-danger",
  };
}
