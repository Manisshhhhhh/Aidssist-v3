import type { ChatMetricData, ChatResult, ChatScalar, ChatTableRow } from "../../types/chat";

type ChatResultRendererProps = {
  result: ChatResult;
};

export function ChatResultRenderer({ result }: ChatResultRendererProps) {
  if (result.type === "text" || result.data === null) {
    return null;
  }

  if (result.type === "metric" && isMetricData(result.data)) {
    return <MetricResult data={result.data} />;
  }

  if (result.type === "list" && isScalarList(result.data)) {
    return <ListResult items={result.data} />;
  }

  if (result.type === "table" && isTableData(result.data)) {
    return <TableResult rows={result.data.slice(0, 20)} />;
  }

  return null;
}

function MetricResult({ data }: { data: ChatMetricData }) {
  return (
    <div className="mt-3 rounded-xl border border-outline bg-surface1 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-muted">
        {data.label}
      </p>
      <p className="mt-2 font-mono text-lg font-semibold text-on-surface">
        {formatValue(data.value)}
      </p>
    </div>
  );
}

function ListResult({ items }: { items: ChatScalar[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.slice(0, 20).map((item, index) => (
        <span
          className="rounded-full border border-outline bg-surface1 px-3 py-1 text-xs text-on-surface-muted"
          key={`${String(item)}-${index}`}
        >
          {formatValue(item)}
        </span>
      ))}
    </div>
  );
}

function TableResult({ rows }: { rows: ChatTableRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="mt-3 rounded-xl border border-outline bg-surface1 p-3 text-sm text-on-surface-muted">
        No rows to display.
      </p>
    );
  }

  const headers = Object.keys(rows[0]);

  return (
    <div className="mt-3 overflow-x-auto rounded-xl border border-outline bg-surface1">
      <table className="min-w-full text-left text-xs">
        <thead className="text-on-surface-muted">
          <tr>
            {headers.map((header) => (
              <th className="border-b border-outline px-3 py-2 font-semibold" key={header}>
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr className="border-b border-outline/70 last:border-0" key={rowIndex}>
              {headers.map((header) => (
                <td className="max-w-48 truncate px-3 py-2 text-on-surface" key={header}>
                  {formatValue(row[header])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function isMetricData(value: ChatResult["data"]): value is ChatMetricData {
  return Boolean(value && typeof value === "object" && !Array.isArray(value) && "label" in value);
}

function isTableData(value: ChatResult["data"]): value is ChatTableRow[] {
  return Array.isArray(value) && value.every((item) => item && typeof item === "object" && !Array.isArray(item));
}

function isScalarList(value: ChatResult["data"]): value is ChatScalar[] {
  return Array.isArray(value) && value.every((item) => item === null || typeof item !== "object");
}

function formatValue(value: ChatMetricData["value"] | ChatScalar | Record<string, ChatScalar>): string {
  if (value === null) {
    return "n/a";
  }

  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, nestedValue]) => `${key}: ${formatValue(nestedValue)}`)
      .join(", ");
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  }

  return String(value);
}
