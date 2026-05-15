import { MessageSquareText } from "lucide-react";

import { SuggestedPrompts } from "./SuggestedPrompts";

type ChatEmptyStateProps = {
  prompts: string[];
  onPromptSelect: (prompt: string) => void;
};

export function ChatEmptyState({ prompts, onPromptSelect }: ChatEmptyStateProps) {
  return (
    <div className="rounded-2xl border border-outline bg-surface1 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="soft-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
          <MessageSquareText size={20} aria-hidden="true" />
        </div>
        <div>
          <h3 className="font-semibold text-on-surface">Ask grounded questions about this dataset</h3>
          <p className="mt-2 text-sm leading-6 text-on-surface-muted">
            I can answer summaries, columns, missing values, aggregations, grouped metrics,
            correlations, charts, and forecast-readiness questions using the uploaded data.
          </p>
          <div className="mt-4">
            <SuggestedPrompts prompts={prompts} onSelect={onPromptSelect} />
          </div>
        </div>
      </div>
    </div>
  );
}
