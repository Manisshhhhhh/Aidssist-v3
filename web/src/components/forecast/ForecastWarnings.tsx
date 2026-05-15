import { AlertTriangle, Info } from "lucide-react";

import { Card } from "../ui/Card";

type ForecastWarningsProps = {
  assumptions: string[];
  warnings: string[];
};

export function ForecastWarnings({ assumptions, warnings }: ForecastWarningsProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <div className="flex items-center gap-2">
          <Info className="text-primary-light" size={18} aria-hidden="true" />
          <h3 className="font-semibold text-on-surface">Assumptions</h3>
        </div>
        {assumptions.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {assumptions.map((assumption) => (
              <li
                className="rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm leading-6 text-on-surface-muted"
                key={assumption}
              >
                {assumption}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface-muted">
            No additional assumptions were returned.
          </p>
        )}
      </Card>

      <Card className={warnings.length > 0 ? "border-warning/25 bg-warning/10" : undefined}>
        <div className="flex items-center gap-2">
          <AlertTriangle className={warnings.length > 0 ? "text-warning" : "text-primary-light"} size={18} aria-hidden="true" />
          <h3 className="font-semibold text-on-surface">Warnings</h3>
        </div>
        {warnings.length > 0 ? (
          <ul className="mt-4 space-y-2">
            {warnings.map((warning) => (
              <li
                className="rounded-xl border border-warning/25 bg-warning/10 px-4 py-3 text-sm leading-6 text-on-surface"
                key={warning}
              >
                {warning}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface-muted">
            No warnings were returned by the forecast engine.
          </p>
        )}
      </Card>
    </div>
  );
}
