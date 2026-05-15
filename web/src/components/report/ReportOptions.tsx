import type { ReportFormat, ReportRequest } from "../../types/report";

type ReportOptionsProps = {
  value: ReportRequest;
  disabled?: boolean;
  onChange: (nextValue: ReportRequest) => void;
};

export function ReportOptions({ disabled = false, onChange, value }: ReportOptionsProps) {
  function setFormat(format: ReportFormat) {
    onChange({ ...value, format });
  }

  function setToggle(
    key: keyof Pick<
      ReportRequest,
      "include_forecast" | "include_charts" | "include_chat_summary" | "include_ai_summary"
    >,
  ) {
    onChange({ ...value, [key]: !value[key] });
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-semibold text-on-surface">Format</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <FormatButton
            active={value.format === "html"}
            disabled={disabled}
            label="HTML report"
            meta="Browser-readable and printable"
            onClick={() => setFormat("html")}
          />
          <FormatButton
            active={value.format === "json"}
            disabled={disabled}
            label="JSON payload"
            meta="Structured report data"
            onClick={() => setFormat("json")}
          />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-4">
        <ToggleRow
          checked={value.include_forecast}
          disabled={disabled}
          label="Forecast summary"
          onChange={() => setToggle("include_forecast")}
        />
        <ToggleRow
          checked={value.include_charts}
          disabled={disabled}
          label="Chart recommendations"
          onChange={() => setToggle("include_charts")}
        />
        <ToggleRow
          checked={value.include_chat_summary}
          disabled={disabled}
          label="Chat summary note"
          onChange={() => setToggle("include_chat_summary")}
        />
        <ToggleRow
          checked={value.include_ai_summary}
          disabled={disabled}
          label="AI summary"
          onChange={() => setToggle("include_ai_summary")}
        />
      </div>
    </div>
  );
}

type FormatButtonProps = {
  active: boolean;
  disabled: boolean;
  label: string;
  meta: string;
  onClick: () => void;
};

function FormatButton({ active, disabled, label, meta, onClick }: FormatButtonProps) {
  return (
    <button
      className={`rounded-xl border p-4 text-left transition ${
        active
          ? "border-primary/55 bg-primary/10 text-on-surface"
          : "border-outline bg-surface1 text-on-surface-muted hover:border-primary/35 hover:text-on-surface"
      } disabled:cursor-not-allowed disabled:opacity-60`}
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      <span className="block text-sm font-semibold">{label}</span>
      <span className="mt-1 block text-xs">{meta}</span>
    </button>
  );
}

type ToggleRowProps = {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: () => void;
};

function ToggleRow({ checked, disabled, label, onChange }: ToggleRowProps) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface">
      <span>{label}</span>
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
