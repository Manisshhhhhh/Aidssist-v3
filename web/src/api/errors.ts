import { ApiClientError } from "./client";

type FriendlyErrorOptions = {
  fallback: string;
  unsupportedFile?: boolean;
};

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export function isUnauthorizedError(error: unknown): boolean {
  return isApiClientError(error) && error.status === 401;
}

export function isReachabilityError(error: unknown): boolean {
  return isApiClientError(error) && (error.status === 0 || isSleepingStatus(error.status));
}

export function getFriendlyApiErrorMessage(
  error: unknown,
  { fallback, unsupportedFile = false }: FriendlyErrorOptions,
): string {
  if (!isApiClientError(error)) {
    return error instanceof Error ? error.message : fallback;
  }

  const requestIdSuffix = error.requestId ? ` Request ID: ${error.requestId}` : "";
  const message = error.rawMessage.toLowerCase();

  if (error.status === 0) {
    return "Unable to reach the backend. It may still be waking up, or the browser blocked the request because of CORS or a network failure.";
  }

  if (isSleepingStatus(error.status)) {
    return `The backend is temporarily unavailable and may be waking up. Please retry in a moment.${requestIdSuffix}`;
  }

  if (error.status === 401 && error.path?.startsWith("/auth/login")) {
    return `${error.rawMessage || "Unable to sign in."}${requestIdSuffix}`;
  }

  if (error.status === 401) {
    return `Sign in required. Please sign in to continue.${requestIdSuffix}`;
  }

  if (error.status === 403) {
    return `You do not have access to this dataset or workspace.${requestIdSuffix}`;
  }

  if (isUnsupportedFileStatus(error.status) && (unsupportedFile || isUnsupportedFileMessage(message))) {
    return `Unsupported file. Upload a CSV or Excel .xlsx file.${requestIdSuffix}`;
  }

  return `${error.rawMessage || fallback}${requestIdSuffix}`;
}

function isSleepingStatus(status: number): boolean {
  return status === 502 || status === 503 || status === 504;
}

function isUnsupportedFileStatus(status: number): boolean {
  return status === 400 || status === 415 || status === 422;
}

function isUnsupportedFileMessage(message: string): boolean {
  return (
    message.includes("csv") ||
    message.includes("excel") ||
    message.includes(".xlsx") ||
    message.includes("unsupported") ||
    message.includes("file is required")
  );
}
