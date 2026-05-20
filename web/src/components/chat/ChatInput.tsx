import { useState } from "react";
import { Loader2, SendHorizontal } from "lucide-react";

import { Button } from "../ui/Button";

type ChatInputProps = {
  disabled?: boolean;
  onSend: (message: string) => void;
};

const maxMessageLength = 500;

export function ChatInput({ disabled = false, onSend }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  function submitMessage() {
    const trimmed = message.trim();

    if (!trimmed) {
      setValidationMessage("Enter a question first.");
      return;
    }

    if (trimmed.length > maxMessageLength) {
      setValidationMessage("Keep questions under 500 characters.");
      return;
    }

    setValidationMessage(null);
    setMessage("");
    onSend(trimmed);
  }

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row">
        <textarea
          aria-label="Ask a question about this dataset"
          className="min-h-12 flex-1 resize-y rounded-xl border border-outline bg-surface1 px-4 py-3 text-sm text-on-surface outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
          disabled={disabled}
          maxLength={maxMessageLength}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submitMessage();
            }
          }}
          placeholder="Ask: average sales by region"
          rows={2}
          value={message}
        />
        <Button className="self-start" disabled={disabled} onClick={submitMessage}>
          {disabled ? (
            <>
              <Loader2 className="animate-spin" size={18} aria-hidden="true" />
              Sending
            </>
          ) : (
            <>
              <SendHorizontal size={18} aria-hidden="true" />
              Send
            </>
          )}
        </Button>
      </div>
      <div className="mt-2 flex items-center justify-between gap-3 text-xs">
        <p className={validationMessage ? "text-danger" : "text-on-surface-muted"}>
          {validationMessage ?? "Enter sends. Shift+Enter adds a new line."}
        </p>
        <span className="text-on-surface-disabled">{message.length}/{maxMessageLength}</span>
      </div>
    </div>
  );
}
