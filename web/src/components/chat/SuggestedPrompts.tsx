type SuggestedPromptsProps = {
  disabled?: boolean;
  prompts: string[];
  onSelect: (prompt: string) => void;
};

export function SuggestedPrompts({ disabled = false, prompts, onSelect }: SuggestedPromptsProps) {
  if (prompts.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {prompts.slice(0, 4).map((prompt) => (
        <button
          className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1.5 text-xs font-semibold text-primary-light transition hover:border-primary/45 hover:bg-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={disabled}
          key={prompt}
          onClick={() => onSelect(prompt)}
          type="button"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
