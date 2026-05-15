import { BarChart3 } from "lucide-react";

type EmptyChartStateProps = {
  message?: string;
};

export function EmptyChartState({ message = "No chart data available." }: EmptyChartStateProps) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center rounded-xl border border-outline bg-surface1 p-6 text-center text-on-surface-muted">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
        <BarChart3 size={22} aria-hidden="true" />
      </div>
      <p className="mt-4 text-sm">{message}</p>
    </div>
  );
}
