import { Fragment, type ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { themeTokens } from "../../theme";
import type { ChartDataPoint, ChartDataResponse } from "../../types/charts";
import { EmptyChartState } from "./EmptyChartState";

type ChartRendererProps = {
  chartData: ChartDataResponse;
  size?: "normal" | "full";
};

const CHART_COLORS = themeTokens.chartPalette;

const axisColor = themeTokens.dark.onSurfaceMuted;
const gridColor = "rgba(160, 160, 160, 0.18)";

export function ChartRenderer({ chartData, size = "normal" }: ChartRendererProps) {
  if (chartData.data.length === 0) {
    return <EmptyChartState />;
  }

  switch (chartData.chart_type) {
    case "bar":
    case "histogram":
      return <BarVisualization chartData={chartData} size={size} />;
    case "line":
      return <LineVisualization chartData={chartData} size={size} />;
    case "area":
      return <AreaVisualization chartData={chartData} size={size} />;
    case "pie":
      return <PieVisualization chartData={chartData} size={size} />;
    case "scatter":
      return <ScatterVisualization chartData={chartData} size={size} />;
    case "heatmap":
      return <HeatmapVisualization chartData={chartData} size={size} />;
    case "box":
      return <BoxVisualization chartData={chartData} size={size} />;
    default:
      return <EmptyChartState message={`Unsupported chart type: ${chartData.chart_type}`} />;
  }
}

function BarVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  return (
    <ChartFrame size={size}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData.data} margin={{ top: 12, right: 12, left: 0, bottom: 24 }}>
          <CartesianGrid stroke={gridColor} vertical={false} />
          <XAxis dataKey="x" tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} width={46} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: colorWithAlpha(CHART_COLORS[0], 0.1) }} />
          <Bar dataKey="y" fill={CHART_COLORS[0]} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function LineVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  return (
    <ChartFrame size={size}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData.data} margin={{ top: 12, right: 12, left: 0, bottom: 24 }}>
          <CartesianGrid stroke={gridColor} vertical={false} />
          <XAxis dataKey="label" tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} width={46} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line dataKey="y" dot={false} stroke={CHART_COLORS[0]} strokeWidth={2.5} type="monotone" />
        </LineChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function AreaVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  return (
    <ChartFrame size={size}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData.data} margin={{ top: 12, right: 12, left: 0, bottom: 24 }}>
          <CartesianGrid stroke={gridColor} vertical={false} />
          <XAxis dataKey="label" tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: axisColor, fontSize: 11 }} tickLine={false} width={46} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            dataKey="y"
            fill={colorWithAlpha(CHART_COLORS[0], 0.22)}
            stroke={CHART_COLORS[0]}
            strokeWidth={2}
            type="monotone"
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function PieVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  return (
    <ChartFrame size={size}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip contentStyle={tooltipStyle} />
          <Pie
            data={chartData.data}
            dataKey="y"
            innerRadius="48%"
            nameKey="label"
            outerRadius="78%"
            paddingAngle={2}
          >
            {chartData.data.map((_, index) => (
              <Cell fill={CHART_COLORS[index % CHART_COLORS.length]} key={`slice-${index}`} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function ScatterVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  return (
    <ChartFrame size={size}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 12, left: 0, bottom: 24 }}>
          <CartesianGrid stroke={gridColor} />
          <XAxis dataKey="x" name={chartData.x} tick={{ fill: axisColor, fontSize: 11 }} />
          <YAxis dataKey="y" name={chartData.y ?? "value"} tick={{ fill: axisColor, fontSize: 11 }} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={chartData.data} fill={CHART_COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartFrame>
  );
}

function HeatmapVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  const xValues = uniqueStrings(chartData.data.map((item) => item.x));
  const yValues = uniqueStrings(chartData.data.map((item) => item.y));

  return (
    <div className={`overflow-x-auto rounded-xl border border-outline bg-surface1 p-4 ${size === "full" ? "min-h-[58vh]" : ""}`}>
      <div
        className="grid min-w-[360px] gap-1"
        style={{ gridTemplateColumns: `96px repeat(${xValues.length}, minmax(56px, 1fr))` }}
      >
        <div />
        {xValues.map((xValue) => (
          <div className="truncate text-center text-xs text-on-surface-muted" key={xValue}>
            {xValue}
          </div>
        ))}
        {yValues.map((yValue) => (
          <Fragment key={yValue}>
            <div className="truncate pr-2 text-right text-xs text-on-surface-muted">
              {yValue}
            </div>
            {xValues.map((xValue) => {
              const value = findHeatmapValue(chartData.data, xValue, yValue);
              const alpha = value === null ? 0.08 : Math.min(0.95, Math.max(0.12, Math.abs(value)));

              return (
                <div
                  className="rounded-lg border border-outline px-2 py-3 text-center font-mono text-xs text-on-surface"
                  key={`${xValue}-${yValue}`}
                  style={{ backgroundColor: colorWithAlpha(CHART_COLORS[0], alpha) }}
                  title={`${xValue}/${yValue}: ${value ?? "n/a"}`}
                >
                  {value === null ? "n/a" : value.toFixed(2)}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
    </div>
  );
}

function BoxVisualization({ chartData, size = "normal" }: ChartRendererProps) {
  const point = chartData.data[0];
  const min = numeric(point.min);
  const q1 = numeric(point.q1);
  const median = numeric(point.median);
  const q3 = numeric(point.q3);
  const max = numeric(point.max);
  const mean = numeric(point.mean);

  if ([min, q1, median, q3, max].some((value) => value === null)) {
    return <EmptyChartState message="Box chart statistics are incomplete." />;
  }

  const minValue = min ?? 0;
  const maxValue = max ?? 1;
  const span = maxValue - minValue || 1;
  const position = (value: number | null) => `${(((value ?? minValue) - minValue) / span) * 100}%`;

  return (
    <div className={`rounded-xl border border-outline bg-surface1 p-5 ${size === "full" ? "min-h-[58vh]" : ""}`}>
      <div className="relative mt-8 h-24">
        <div className="absolute left-0 right-0 top-1/2 h-px bg-on-surface-disabled/50" />
        <div
          className="absolute top-1/2 h-12 -translate-y-1/2 rounded-lg border border-primary/60 bg-primary/15"
          style={{ left: position(q1), width: `calc(${position(q3)} - ${position(q1)})` }}
        />
        {[min, median, max].map((value, index) => (
          <div
            className="absolute top-1/2 h-16 w-0.5 -translate-y-1/2 bg-primary-light"
            key={`${value}-${index}`}
            style={{ left: position(value) }}
          />
        ))}
        {mean !== null ? (
          <div
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-warning"
            style={{ left: position(mean) }}
            title={`Mean: ${mean}`}
          />
        ) : null}
      </div>

      <div className="grid gap-2 text-xs text-on-surface-muted sm:grid-cols-3">
        <Stat label="Min" value={min} />
        <Stat label="Median" value={median} />
        <Stat label="Max" value={max} />
        <Stat label="Q1" value={q1} />
        <Stat label="Q3" value={q3} />
        <Stat label="Outliers" value={numeric(point.outlier_count)} />
      </div>
    </div>
  );
}

function ChartFrame({ children, size }: { children: ReactNode; size: "normal" | "full" }) {
  return (
    <div className={`${size === "full" ? "h-[62vh] min-h-[420px]" : "h-72"} rounded-xl border border-outline bg-surface1 p-3`}>
      {children}
    </div>
  );
}


function Stat({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-lg bg-surface2 px-3 py-2">
      <p className="text-[10px] uppercase tracking-[0.12em] text-on-surface-disabled">{label}</p>
      <p className="mt-1 font-mono text-on-surface">{value === null ? "n/a" : formatNumber(value)}</p>
    </div>
  );
}

function uniqueStrings(values: Array<string | number | null | undefined>): string[] {
  return Array.from(new Set(values.map((value) => String(value ?? "n/a"))));
}

function findHeatmapValue(data: ChartDataPoint[], xValue: string, yValue: string): number | null {
  const point = data.find((item) => String(item.x) === xValue && String(item.y) === yValue);
  return numeric(point?.value);
}

function numeric(value: string | number | null | undefined): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
}

const tooltipStyle = {
  backgroundColor: themeTokens.dark.surface1,
  border: `1px solid ${themeTokens.dark.outline}`,
  borderRadius: "12px",
  color: themeTokens.dark.onSurface,
};

function colorWithAlpha(hexColor: string, alpha: number): string {
  const normalized = hexColor.replace("#", "");
  const red = Number.parseInt(normalized.slice(0, 2), 16);
  const green = Number.parseInt(normalized.slice(2, 4), 16);
  const blue = Number.parseInt(normalized.slice(4, 6), 16);

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
