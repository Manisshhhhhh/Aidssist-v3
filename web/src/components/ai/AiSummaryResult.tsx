import type { AiSummaryResponse } from "../../types/llm";
import { Badge } from "../ui/Badge";

type AiSummaryResultProps = {
  summary: AiSummaryResponse;
};

export function AiSummaryResult({ summary }: AiSummaryResultProps) {
  return (
    <div className="space-y-4 rounded-xl border border-primary/25 bg-primary/5 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{summary.provider}</Badge>
        <Badge>{summary.model}</Badge>
        <Badge>Raw rows sent: {summary.grounding.raw_rows_sent ? "yes" : "no"}</Badge>
      </div>
      <div className="whitespace-pre-wrap text-sm leading-7 text-on-surface">{summary.summary}</div>
      {summary.warnings.length ? (
        <ul className="list-disc space-y-1 pl-5 text-xs leading-5 text-on-surface-muted">
          {summary.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
