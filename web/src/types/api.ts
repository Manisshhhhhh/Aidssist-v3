export type ApiError = {
  status: number;
  message: string;
  requestId?: string | null;
  details?: unknown;
  path?: string;
};

export type HealthResponse = {
  status: string;
  app_name: string;
  version: string;
  environment: string;
};
