import { BadgeCheck, CopyMinus, Rows3, Table2, TriangleAlert } from "lucide-react";

import type { AnalysisResponse } from "../../types/analysis";
import { Card } from "../ui/Card";

type DatasetOverviewCardsProps = {
  analysis: AnalysisResponse;
};

export function DatasetOverviewCards({ analysis }: DatasetOverviewCardsProps) {
  const cards = [
    { label: "Rows", value: analysis.row_count, icon: Rows3 },
    { label: "Columns", value: analysis.column_count, icon: Table2 },
    { label: "Missing cells", value: analysis.quality.missing_cells, icon: TriangleAlert },
    { label: "Duplicate rows", value: analysis.quality.duplicate_rows, icon: CopyMinus },
    { label: "Quality score", value: `${analysis.quality.quality_score}/100`, icon: BadgeCheck },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((item) => {
        const Icon = item.icon;

        return (
          <Card className="p-4" key={item.label}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-on-surface-muted">
                  {item.label}
                </p>
                <p className="mt-2 text-3xl font-semibold text-on-surface">
                  {formatCardValue(item.value)}
                </p>
              </div>
              <div className="soft-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
                <Icon size={20} aria-hidden="true" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

function formatCardValue(value: number | string): string {
  return typeof value === "number" ? value.toLocaleString() : value;
}
