import { useState } from "react";
import { AlertCircle, Loader2, Sparkles } from "lucide-react";

import { createAiSummary } from "../../api/llm";
import type { AnalysisResponse } from "../../types/analysis";
import type { AiSummaryRequest, AiSummaryResponse } from "../../types/llm";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { AiSummaryEmptyState } from "./AiSummaryEmptyState";
import { AiSummaryOptions } from "./AiSummaryOptions";
import { AiSummaryResult } from "./AiSummaryResult";

type AiSummaryPanelProps = {
  datasetId: string;
  analysis?: AnalysisResponse | null;
};

const defaultRequest: AiSummaryRequest = {
  include_forecast: true,
  include_charts: true,
  tone: "executive",
  format: "bullets",
};

export function AiSummaryPanel({ analysis, datasetId }: AiSummaryPanelProps) {
  const [options, setOptions] = useState<AiSummaryRequest>(defaultRequest);
  const [summary, setSummary] = useState<AiSummaryResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!analysis || isGenerating) {
      return;
    }
    setIsGenerating(true);
    setError(null);
    try {
      setSummary(await createAiSummary(datasetId, options));
    } catch (summaryError) {
      setError(summaryError instanceof Error ? summaryError.message : "Unable to generate AI summary.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <Card>
      <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            AI explanation
          </p>
          <h2 className="mt-2 text-xl font-semibold text-on-surface">AI Summary</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-on-surface-muted">
            Generated from Aidssist’s deterministic analysis outputs. Optional Gemini assistance
            adds narrative only; deterministic metrics remain the source of truth.
          </p>
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
          <Sparkles size={20} aria-hidden="true" />
        </div>
      </div>

      {!analysis ? <AiSummaryEmptyState /> : null}

      {analysis ? (
        <div className="space-y-5">
          <AiSummaryOptions disabled={isGenerating} onChange={setOptions} value={options} />
          {error ? (
            <div className="flex items-start gap-3 rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-on-surface">
              <AlertCircle className="mt-0.5 shrink-0 text-danger" size={18} aria-hidden="true" />
              <p>{error}</p>
            </div>
          ) : null}
          {summary ? <AiSummaryResult summary={summary} /> : <AiSummaryEmptyState />}
          <Button disabled={isGenerating} onClick={() => void handleGenerate()}>
            {isGenerating ? <Loader2 className="animate-spin" size={18} aria-hidden="true" /> : null}
            Generate AI summary
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
