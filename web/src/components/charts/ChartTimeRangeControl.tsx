import type { ChartTimeRange } from "../../types/charts";

type ChartTimeRangeControlProps = {
  disabled?: boolean;
  value: ChartTimeRange;
  onChange: (value: ChartTimeRange) => void;
};

const ranges: Array<{ label: string; value: ChartTimeRange }> = [
  { label: "All", value: "all" },
  { label: "1D", value: "1d" },
  { label: "1W", value: "1w" },
  { label: "1M", value: "1m" },
  { label: "1Q", value: "1q" },
  { label: "1Y", value: "1y" },
  { label: "3Y", value: "3y" },
  { label: "5Y", value: "5y" },
];

export function ChartTimeRangeControl({
  disabled = false,
  onChange,
  value,
}: ChartTimeRangeControlProps) {
  return (
    <div aria-label="Chart time period" className="flex flex-wrap gap-1" role="group">
      {ranges.map((range) => (
        <button
          className={[
            "min-h-8 rounded-lg border px-2.5 text-xs font-semibold transition",
            value === range.value
              ? "border-primary/60 bg-primary/15 text-primary-light"
              : "border-outline bg-surface1 text-on-surface-muted hover:border-primary/35 hover:text-on-surface",
          ].join(" ")}
          disabled={disabled}
          key={range.value}
          onClick={() => onChange(range.value)}
          type="button"
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}
