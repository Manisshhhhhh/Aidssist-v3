import type { AiSummaryFormat, AiSummaryRequest, AiSummaryTone } from "../../types/llm";

type AiSummaryOptionsProps = {
  value: AiSummaryRequest;
  disabled?: boolean;
  onChange: (nextValue: AiSummaryRequest) => void;
};

export function AiSummaryOptions({ disabled = false, onChange, value }: AiSummaryOptionsProps) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <label className="space-y-2 text-sm text-on-surface">
        <span className="font-semibold">Tone</span>
        <select
          className="w-full rounded-xl border border-outline bg-surface1 px-3 py-2 text-on-surface focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25"
          disabled={disabled}
          value={value.tone}
          onChange={(event) => onChange({ ...value, tone: event.target.value as AiSummaryTone })}
        >
          <option value="executive">Executive</option>
          <option value="analyst">Analyst</option>
          <option value="concise">Concise</option>
        </select>
      </label>
      <label className="space-y-2 text-sm text-on-surface">
        <span className="font-semibold">Format</span>
        <select
          className="w-full rounded-xl border border-outline bg-surface1 px-3 py-2 text-on-surface focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/25"
          disabled={disabled}
          value={value.format}
          onChange={(event) => onChange({ ...value, format: event.target.value as AiSummaryFormat })}
        >
          <option value="bullets">Bullets</option>
          <option value="narrative">Narrative</option>
        </select>
      </label>
      <Toggle
        checked={value.include_forecast}
        disabled={disabled}
        label="Use forecast"
        onChange={() => onChange({ ...value, include_forecast: !value.include_forecast })}
      />
      <Toggle
        checked={value.include_charts}
        disabled={disabled}
        label="Use charts"
        onChange={() => onChange({ ...value, include_charts: !value.include_charts })}
      />
    </div>
  );
}

type ToggleProps = {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: () => void;
};

function Toggle({ checked, disabled, label, onChange }: ToggleProps) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface">
      <span className="font-semibold">{label}</span>
      <input
        checked={checked}
        className="h-4 w-4 accent-primary"
        disabled={disabled}
        onChange={onChange}
        type="checkbox"
      />
    </label>
  );
}
