export type ApiError = {
  status: number;
  message: string;
  requestId?: string | null;
  details?: unknown;
};

export type HealthResponse = {
  status: string;
  app_name: string;
  version: string;
  environment: string;
};
