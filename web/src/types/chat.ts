export type ChatResultType = "text" | "table" | "metric" | "list";

export type ChatScalar = string | number | boolean | null;

export type ChatTableRow = Record<string, ChatScalar>;

export interface ChatMetricData {
  label: string;
  value: ChatScalar | Record<string, ChatScalar>;
}

export interface ChatResult {
  type: ChatResultType;
  data: ChatTableRow[] | ChatMetricData | ChatScalar[] | string | null;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  dataset_id: string;
  conversation_id: string;
  message: string;
  answer: string;
  intent: string;
  confidence: number;
  columns_used: string[];
  result: ChatResult;
  suggested_followups: string[];
  warnings: string[];
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  isLoading?: boolean;
  error?: string;
}
