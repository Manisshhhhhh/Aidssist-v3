import type { ApiError } from "../types/api";

export const API_BASE_URL = resolveApiBaseUrl();
const API_KEY = import.meta.env.VITE_AIDSSIST_API_KEY;
export const AUTH_TOKEN_STORAGE_KEY = "aidssist_access_token";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | Record<string, unknown> | null;
};

export class ApiClientError extends Error {
  status: number;
  requestId?: string | null;
  details?: unknown;

  constructor(error: ApiError) {
    super(error.requestId ? `${error.message} Request ID: ${error.requestId}` : error.message);
    this.name = "ApiClientError";
    this.status = error.status;
    this.requestId = error.requestId;
    this.details = error.details;
  }
}

export async function apiRequest<TResponse>(
  path: string,
  options: RequestOptions = {},
): Promise<TResponse> {
  const headers = new Headers(options.headers);
  applyDefaultHeaders(headers);
  let body = options.body;

  if (body && isJsonBody(body)) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(body);
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${normalizePath(path)}`, {
      ...options,
      headers,
      body,
    });
  } catch (error) {
    throw new ApiClientError({
      status: 0,
      message: "Unable to reach the Aidssist API. Check that the backend is running.",
      details: error,
    });
  }

  const payload = await parseResponse(response);
  const requestId = response.headers.get("X-Request-ID") || getPayloadRequestId(payload);

  if (!response.ok) {
    const message =
      getErrorMessage(payload) || `Request failed with status ${response.status}`;

    throw new ApiClientError({
      status: response.status,
      message,
      requestId,
      details: payload,
    });
  }

  return payload as TResponse;
}

export async function apiBlobRequest(
  path: string,
  options: Omit<RequestInit, "body"> = {},
): Promise<Blob> {
  const headers = new Headers(options.headers);
  applyDefaultHeaders(headers);

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${normalizePath(path)}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new ApiClientError({
      status: 0,
      message: "Unable to reach the Aidssist API. Check that the backend is running.",
      details: error,
    });
  }

  if (!response.ok) {
    const payload = await parseResponse(response);
    const requestId = response.headers.get("X-Request-ID") || getPayloadRequestId(payload);
    throw new ApiClientError({
      status: response.status,
      message: getErrorMessage(payload) || `Request failed with status ${response.status}`,
      requestId,
      details: payload,
    });
  }

  return response.blob();
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

function applyDefaultHeaders(headers: Headers): void {
  if (API_KEY) {
    headers.set("X-Aidssist-API-Key", API_KEY);
  }
  const token = getStoredAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function setStoredAccessToken(token: string): void {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function clearStoredAccessToken(): void {
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

function resolveApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL;

  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, "");
  }

  if (typeof window !== "undefined" && window.location.hostname) {
    const hostname =
      window.location.hostname === "0.0.0.0" ? "127.0.0.1" : window.location.hostname;

    return `http://${hostname}:8000`;
  }

  return "http://127.0.0.1:8000";
}

function isJsonBody(body: RequestOptions["body"]): body is Record<string, unknown> {
  return (
    Boolean(body) &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof Blob) &&
    !(body instanceof ArrayBuffer)
  );
}

async function parseResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function getErrorMessage(payload: unknown): string | null {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }

  if (typeof payload === "string") {
    return payload;
  }

  return null;
}

function getPayloadRequestId(payload: unknown): string | null {
  if (payload && typeof payload === "object" && "request_id" in payload) {
    const requestId = (payload as { request_id?: unknown }).request_id;
    return typeof requestId === "string" ? requestId : null;
  }

  return null;
}
