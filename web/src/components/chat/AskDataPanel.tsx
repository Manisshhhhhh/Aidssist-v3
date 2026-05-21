import { useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";

import { getFriendlyApiErrorMessage } from "../../api/errors";
import { askDataset } from "../../api/chat";
import type { AnalysisResponse } from "../../types/analysis";
import type { ChatMessage } from "../../types/chat";
import { Card } from "../ui/Card";
import { ChatEmptyState } from "./ChatEmptyState";
import { ChatInput } from "./ChatInput";
import { ChatMessageBubble } from "./ChatMessageBubble";

type AskDataPanelProps = {
  analysis?: AnalysisResponse;
  datasetId: string;
};

export function AskDataPanel({ analysis, datasetId }: AskDataPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [isSending, setIsSending] = useState(false);

  const defaultPrompts = useMemo(() => buildDefaultPrompts(analysis), [analysis]);

  async function sendMessage(content: string) {
    if (isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content,
    };
    const loadingMessage: ChatMessage = {
      id: createMessageId(),
      role: "assistant",
      content: "",
      isLoading: true,
    };

    setMessages((current) => [...current, userMessage, loadingMessage]);
    setIsSending(true);

    try {
      const response = await askDataset(datasetId, {
        conversation_id: conversationId,
        message: content,
      });
      setConversationId(response.conversation_id);
      setMessages((current) =>
        current.map((message) =>
          message.id === loadingMessage.id
            ? {
                id: loadingMessage.id,
                role: "assistant",
                content: response.answer,
                response,
              }
            : message,
        ),
      );
    } catch (error) {
      setMessages((current) =>
        current.map((message) =>
          message.id === loadingMessage.id
            ? {
                id: loadingMessage.id,
                role: "assistant",
                content: "I could not answer that question.",
                error: getFriendlyApiErrorMessage(error, {
                  fallback: "Unable to reach the chat endpoint.",
                }),
              }
            : message,
        ),
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <Card>
      <div className="mb-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Ask your data
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Dataset Q&A</h2>
        <p className="mt-2 text-sm leading-6 text-on-surface-muted">
          Answers are deterministic and grounded in the uploaded CSV plus analysis output. No
          arbitrary code, SQL, or external AI is used.
        </p>
      </div>

      <div className="space-y-4">
        {messages.length === 0 ? (
          <ChatEmptyState prompts={defaultPrompts} onPromptSelect={(prompt) => void sendMessage(prompt)} />
        ) : (
          <div className="max-h-[620px] space-y-3 overflow-y-auto pr-1">
            <AnimatePresence initial={false}>
              {messages.map((message) => (
                <ChatMessageBubble
                  key={message.id}
                  message={message}
                  onFollowupSelect={(prompt) => void sendMessage(prompt)}
                />
              ))}
            </AnimatePresence>
          </div>
        )}

        <ChatInput disabled={isSending} onSend={(message) => void sendMessage(message)} />
      </div>
    </Card>
  );
}

function buildDefaultPrompts(analysis?: AnalysisResponse): string[] {
  const prompts = ["Summarize this dataset", "Which columns have missing values?", "What charts should I use?"];

  if (!analysis) {
    return prompts;
  }

  const numeric = analysis.columns.find((column) => column.semantic_type === "numeric");
  const categorical = analysis.columns.find((column) =>
    ["categorical", "boolean", "text"].includes(column.semantic_type),
  );
  const datetime = analysis.columns.find((column) => column.semantic_type === "datetime");

  if (numeric && categorical) {
    prompts.push(`Average ${numeric.name} by ${categorical.name}`);
  }

  if (numeric && datetime) {
    prompts.push(`Can I forecast ${numeric.name}?`);
  }

  return prompts.slice(0, 4);
}

function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
