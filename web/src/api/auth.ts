import { apiRequest } from "./client";
import type { AuthStatusResponse, AuthUser, LoginRequest, LoginResponse, RegisterRequest } from "../types/auth";

export function getAuthStatus(): Promise<AuthStatusResponse> {
  return apiRequest<AuthStatusResponse>("/auth/status");
}

export function registerUser(request: RegisterRequest): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/register", {
    method: "POST",
    body: { ...request },
  });
}

export function loginUser(request: LoginRequest): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: { ...request },
  });
}

export function getCurrentUser(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}
