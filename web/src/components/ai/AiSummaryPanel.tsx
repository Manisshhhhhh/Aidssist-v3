import { useState } from "react";
import { AlertCircle, Loader2, Sparkles } from "lucide-react";

import { getFriendlyApiErrorMessage } from "../../api/errors";
import { createAiSummary } from "../../api/llm";
import { useAuth } from "../../auth/useAuth";
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
  const { status } = useAuth();
  const [options, setOptions] = useState<AiSummaryRequest>(defaultRequest);
  const [summary, setSummary] = useState<AiSummaryResponse | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const llmStatusKnown = Boolean(status);
  const isLlmConfigured = Boolean(status?.llm_enabled && status.llm_key_configured);
  const isActionDisabled = isGenerating || !isLlmConfigured;
  const setupMessage = getLlmSetupMessage(status);

  async function handleGenerate() {
    if (!analysis || isActionDisabled) {
      return;
    }
    setIsGenerating(true);
    setError(null);
    try {
      setSummary(await createAiSummary(datasetId, options));
    } catch (summaryError) {
      setError(getFriendlyApiErrorMessage(summaryError, { fallback: "Unable to generate AI summary." }));
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
          <AiSummaryOptions disabled={isActionDisabled} onChange={setOptions} value={options} />
          {setupMessage ? (
            <div className="flex items-start gap-3 rounded-xl border border-outline bg-surface-container/70 p-4 text-sm text-on-surface-muted">
              <Sparkles className="mt-0.5 shrink-0 text-primary-light" size={18} aria-hidden="true" />
              <p>{setupMessage}</p>
            </div>
          ) : null}
          {error ? (
            <div className="flex items-start gap-3 rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-on-surface">
              <AlertCircle className="mt-0.5 shrink-0 text-danger" size={18} aria-hidden="true" />
              <p>{error}</p>
            </div>
          ) : null}
          {summary ? <AiSummaryResult summary={summary} /> : <AiSummaryEmptyState />}
          <Button disabled={!llmStatusKnown || isActionDisabled} onClick={() => void handleGenerate()}>
            {isGenerating ? <Loader2 className="animate-spin" size={18} aria-hidden="true" /> : null}
            Generate AI summary
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

function getLlmSetupMessage(status: ReturnType<typeof useAuth>["status"]): string | null {
  if (!status) {
    return "Checking AI summary availability...";
  }
  if (!status.llm_enabled) {
    return "AI summaries are disabled on this deployment. Enable AIDSSIST_LLM_ENABLED on the backend and configure a fresh Gemini API key to use this panel.";
  }
  if (!status.llm_key_configured) {
    return "AI summaries are enabled, but GEMINI_API_KEY is not configured on the backend.";
  }
  return null;
}
