import { Loader2 } from "lucide-react";
import { motion } from "framer-motion";

import type { ChatMessage } from "../../types/chat";
import { Badge } from "../ui/Badge";
import { ChatResultRenderer } from "./ChatResultRenderer";
import { SuggestedPrompts } from "./SuggestedPrompts";

type ChatMessageBubbleProps = {
  message: ChatMessage;
  onFollowupSelect: (prompt: string) => void;
};

export function ChatMessageBubble({ message, onFollowupSelect }: ChatMessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
      initial={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
    >
      <div
        className={[
          "max-w-[92%] rounded-2xl border px-4 py-3 text-sm leading-6 sm:max-w-[82%]",
          isUser
            ? "border-primary/30 bg-primary/15 text-on-surface"
            : "border-outline bg-surface1 text-on-surface-muted",
        ].join(" ")}
      >
        {message.isLoading ? (
          <div className="flex items-center gap-2 text-on-surface-muted">
            <Loader2 className="animate-spin text-primary-light" size={16} aria-hidden="true" />
            Thinking through the dataset
          </div>
        ) : (
          <p className={isUser ? "text-on-surface" : "text-on-surface-muted"}>{message.content}</p>
        )}

        {message.error ? (
          <p className="mt-3 rounded-xl border border-danger/25 bg-danger/10 px-3 py-2 text-danger">
            {message.error}
          </p>
        ) : null}

        {message.response ? (
          <div className="mt-3">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge className="tracking-normal">{message.response.intent}</Badge>
              <span className="rounded-full border border-outline bg-surface2 px-2.5 py-1 text-xs text-on-surface-muted">
                Confidence {Math.round(message.response.confidence * 100)}%
              </span>
            </div>
            <ChatResultRenderer result={message.response.result} />
            {message.response.warnings.length > 0 ? (
              <div className="mt-3 space-y-2">
                {message.response.warnings.map((warning) => (
                  <p
                    className="rounded-xl border border-warning/25 bg-warning/10 px-3 py-2 text-xs text-on-surface"
                    key={warning}
                  >
                    {warning}
                  </p>
                ))}
              </div>
            ) : null}
            <div className="mt-4">
              <SuggestedPrompts
                prompts={message.response.suggested_followups}
                onSelect={onFollowupSelect}
              />
            </div>
          </div>
        ) : null}
      </div>
    </motion.article>
  );
}
