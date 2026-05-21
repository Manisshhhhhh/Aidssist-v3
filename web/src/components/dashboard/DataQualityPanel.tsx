import type { DataQuality } from "../../types/analysis";
import { Card } from "../ui/Card";

type DataQualityPanelProps = {
  quality: DataQuality;
};

export function DataQualityPanel({ quality }: DataQualityPanelProps) {
  const tone = getQualityTone(quality.quality_score);
  const issueBreakdown = quality.issue_breakdown ?? [];

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
            Deterministic score based on missingness, duplicates, type clarity, cardinality,
            date parsing, constant columns, and potential outliers.
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
        <ColumnList label="Unclear type columns" columns={quality.invalid_type_columns ?? []} />
        <ColumnList label="High-cardinality columns" columns={quality.high_cardinality_columns ?? []} />
        <ColumnList label="Date parsing issues" columns={quality.date_parse_issue_columns ?? []} />
        <ColumnList label="Potential outlier columns" columns={quality.outlier_columns ?? []} />
      </div>

      <div className="mt-5 space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-disabled">
          Issue breakdown
        </p>
        {issueBreakdown.length > 0 ? (
          issueBreakdown.map((issue) => (
            <div
              className="rounded-xl border border-outline bg-surface1 p-4 text-sm"
              key={`${issue.type}-${issue.title}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${getIssueTone(issue.severity)}`}>
                  {issue.severity}
                </span>
                <p className="font-semibold text-on-surface">{issue.title}</p>
              </div>
              <p className="mt-2 text-on-surface-muted">{issue.message}</p>
              {(issue.columns ?? []).length > 0 ? (
                <p className="mt-2 text-xs text-on-surface-disabled">{issue.columns.join(", ")}</p>
              ) : null}
            </div>
          ))
        ) : (
          <div className="rounded-xl border border-success/25 bg-success/10 p-4 text-sm text-success">
            No material quality issues detected.
          </div>
        )}
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
      label: "Excellent",
      badge: "border-success/25 bg-success/10 text-success",
      bar: "bg-success",
    };
  }

  if (score >= 75) {
    return {
      label: "Good",
      badge: "border-warning/25 bg-warning/10 text-warning",
      bar: "bg-warning",
    };
  }

  if (score >= 60) {
    return {
      label: "Fair",
      badge: "border-warning/25 bg-warning/10 text-warning",
      bar: "bg-warning",
    };
  }

  return {
    label: "Poor",
    badge: "border-danger/25 bg-danger/10 text-danger",
    bar: "bg-danger",
  };
}

function getIssueTone(severity: string): string {
  if (severity === "high") return "border-danger/25 bg-danger/10 text-danger";
  if (severity === "medium") return "border-warning/25 bg-warning/10 text-warning";
  return "border-outline bg-surface2 text-on-surface-muted";
}
