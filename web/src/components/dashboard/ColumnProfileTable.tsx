import type { ColumnProfile, ColumnStats } from "../../types/analysis";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

type ColumnProfileTableProps = {
  columns: ColumnProfile[];
};

export function ColumnProfileTable({ columns }: ColumnProfileTableProps) {
  return (
    <Card>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Column profiles
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Detected structure</h2>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-[920px] w-full border-separate border-spacing-y-2 text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.12em] text-on-surface-disabled">
            <tr>
              <th className="px-3 py-2">Column</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Missing</th>
              <th className="px-3 py-2">Unique</th>
              <th className="px-3 py-2">Samples</th>
              <th className="px-3 py-2">Key stats</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr className="rounded-xl bg-surface1 transition hover:bg-surface3" key={column.name}>
                <td className="max-w-52 rounded-l-lg px-3 py-3">
                  <p className="truncate font-semibold text-on-surface">{column.name}</p>
                  <p className="mt-1 text-xs text-on-surface-disabled">{column.dtype}</p>
                </td>
                <td className="px-3 py-3">
                  <Badge className="tracking-normal">{column.semantic_type}</Badge>
                </td>
                <td className="px-3 py-3 text-on-surface-muted">{column.missing_percent}%</td>
                <td className="px-3 py-3 text-on-surface-muted">{column.unique_count.toLocaleString()}</td>
                <td className="max-w-56 px-3 py-3 text-on-surface-muted">
                  <span className="line-clamp-2">{formatSamples(column.sample_values)}</span>
                </td>
                <td className="rounded-r-lg px-3 py-3 text-on-surface-muted">
                  {formatStats(column.stats)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function formatSamples(samples: ColumnProfile["sample_values"]): string {
  if (samples.length === 0) {
    return "No samples";
  }

  return samples.map((sample) => (sample === null ? "null" : String(sample))).join(", ");
}

function formatStats(stats: ColumnStats): string {
  if (typeof stats.mean === "number") {
    return `mean ${formatNumber(stats.mean)} · median ${formatOptionalNumber(stats.median)} · range ${formatOptionalNumber(stats.min)}-${formatOptionalNumber(stats.max)}`;
  }

  if (stats.top_values?.length) {
    const top = stats.top_values[0];
    return `top ${String(top.value)} (${top.percent}%)`;
  }

  if (stats.min_date || stats.max_date) {
    return `${formatDate(stats.min_date)} to ${formatDate(stats.max_date)} · ${stats.range_days ?? 0} days`;
  }

  if (typeof stats.average_length === "number") {
    return `avg length ${formatNumber(stats.average_length)} · min ${formatOptionalNumber(stats.min_length)} · max ${formatOptionalNumber(stats.max_length)}`;
  }

  return "No summary";
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
}

function formatOptionalNumber(value: number | null | undefined): string {
  return typeof value === "number" ? formatNumber(value) : "n/a";
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "n/a";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}
