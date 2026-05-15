import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { themeTokens } from "../../theme";
import type { ForecastResponse } from "../../types/forecast";
import { Card } from "../ui/Card";

type ForecastChartProps = {
  forecast: ForecastResponse;
};

type ForecastChartRow = {
  date: string;
  label: string;
  historicalValue: number | null;
  forecastValue: number | null;
  confidenceBand: [number, number] | null;
  separator?: string;
};

const palette = themeTokens.chartPalette;
const axisColor = themeTokens.dark.onSurfaceMuted;
const gridColor = "rgba(160, 160, 160, 0.18)";

export function ForecastChart({ forecast }: ForecastChartProps) {
  const rows = buildForecastRows(forecast);
  const separatorDate = forecast.forecast_points[0]?.date;

  if (rows.length === 0) {
    return (
      <Card>
        <p className="text-sm text-on-surface-muted">No forecast points were returned.</p>
      </Card>
    );
  }

  return (
    <Card>
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Forecast chart
          </p>
          <h3 className="mt-2 text-xl font-semibold text-on-surface">
            {forecast.target_column} over {forecast.date_column}
          </h3>
        </div>
        <p className="text-xs text-on-surface-muted">
          {formatModelName(forecast.model_used)} · {forecast.frequency}
        </p>
      </div>

      <div className="h-[360px] rounded-xl border border-outline bg-surface1 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 16, right: 12, left: 0, bottom: 22 }}>
            <CartesianGrid stroke={gridColor} vertical={false} />
            <XAxis
              dataKey="label"
              minTickGap={24}
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
            />
            <YAxis tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} width={48} />
            <Tooltip content={<ForecastTooltip />} cursor={{ stroke: palette[2], strokeOpacity: 0.35 }} />
            <Legend wrapperStyle={{ color: axisColor, fontSize: 12 }} />
            {separatorDate ? (
              <ReferenceLine
                label={{ fill: axisColor, fontSize: 11, position: "insideTopRight", value: "Forecast" }}
                stroke={palette[2]}
                strokeDasharray="4 4"
                x={formatDateLabel(separatorDate)}
              />
            ) : null}
            <Area
              dataKey="confidenceBand"
              fill={colorWithAlpha(palette[0], 0.16)}
              legendType="none"
              name="Confidence band"
              stroke="none"
              type="monotone"
            />
            <Line
              connectNulls={false}
              dataKey="historicalValue"
              dot={false}
              name="Historical"
              stroke={palette[0]}
              strokeWidth={2.5}
              type="monotone"
            />
            <Line
              connectNulls={false}
              dataKey="forecastValue"
              dot={{ fill: palette[1], r: 3, strokeWidth: 0 }}
              name="Forecast"
              stroke={palette[1]}
              strokeDasharray="6 5"
              strokeWidth={2.5}
              type="monotone"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function buildForecastRows(forecast: ForecastResponse): ForecastChartRow[] {
  const historicalRows = forecast.historical_points.map((point) => ({
    date: point.date,
    label: formatDateLabel(point.date),
    historicalValue: point.value,
    forecastValue: null,
    confidenceBand: null,
  }));

  const forecastRows = forecast.forecast_points.map((point) => ({
    date: point.date,
    label: formatDateLabel(point.date),
    historicalValue: null,
    forecastValue: point.predicted_value,
    confidenceBand:
      point.lower_bound !== null && point.upper_bound !== null
        ? ([point.lower_bound, point.upper_bound] as [number, number])
        : null,
  }));

  return [...historicalRows, ...forecastRows];
}

function ForecastTooltip({
  active,
  label,
  payload,
}: {
  active?: boolean;
  label?: string;
  payload?: Array<{ name?: string; value?: unknown; color?: string }>;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const rows = payload.filter((item) => item.value !== null && item.value !== undefined);

  return (
    <div className="rounded-xl border border-outline bg-surface2 px-4 py-3 text-sm shadow-panel">
      <p className="mb-2 font-semibold text-on-surface">{label}</p>
      <div className="space-y-1">
        {rows.map((item) => (
          <p className="flex items-center gap-2 text-on-surface-muted" key={item.name}>
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: item.color ?? palette[0] }}
            />
            {item.name}: <span className="font-mono text-on-surface">{formatTooltipValue(item.value)}</span>
          </p>
        ))}
      </div>
    </div>
  );
}

function formatTooltipValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map((item) => formatTooltipValue(item)).join(" - ");
  }

  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  }

  return String(value);
}

function formatDateLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  }).format(date);
}

function formatModelName(model: string): string {
  return model
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function colorWithAlpha(hexColor: string, alpha: number): string {
  const normalized = hexColor.replace("#", "");
  const red = Number.parseInt(normalized.slice(0, 2), 16);
  const green = Number.parseInt(normalized.slice(2, 4), 16);
  const blue = Number.parseInt(normalized.slice(4, 6), 16);

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
