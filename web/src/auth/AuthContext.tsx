import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { getAuthStatus, getCurrentUser, loginUser, registerUser } from "../api/auth";
import {
  AUTH_REQUIRED_EVENT,
  clearStoredAccessToken,
  getStoredAccessToken,
  setStoredAccessToken,
} from "../api/client";
import type { AuthStatusResponse, AuthUser, LoginRequest, RegisterRequest } from "../types/auth";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  status: AuthStatusResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authRequiredMessage: string | null;
  login: (request: LoginRequest) => Promise<void>;
  register: (request: RegisterRequest) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredAccessToken());
  const [status, setStatus] = useState<AuthStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authRequiredMessage, setAuthRequiredMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadAuth() {
      setIsLoading(true);
      try {
        const authStatus = await getAuthStatus();
        if (cancelled) return;
        setStatus(authStatus);

        const storedToken = getStoredAccessToken();
        setToken(storedToken);
        if (authStatus.user_auth_enabled && storedToken) {
          try {
            setUser(await getCurrentUser());
          } catch {
            clearStoredAccessToken();
            setToken(null);
            setUser(null);
          }
        }
      } catch {
        if (!cancelled) {
          setStatus(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadAuth();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    async function handleAuthRequired(event: Event) {
      const detail = (event as CustomEvent<{ path?: string }>).detail;
      const path = detail?.path ?? "";

      if (
        path.startsWith("/auth/login") ||
        path.startsWith("/auth/register") ||
        path.startsWith("/auth/status")
      ) {
        return;
      }

      let nextStatus = status;
      try {
        nextStatus = await getAuthStatus();
        setStatus(nextStatus);
      } catch {
        // Keep the last known status. The gate should only switch to auth when the server says auth is enabled.
      }

      if (!nextStatus?.user_auth_enabled) {
        return;
      }

      clearStoredAccessToken();
      setToken(null);
      setUser(null);
      setAuthRequiredMessage("Sign in required");
    }

    window.addEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    return () => {
      window.removeEventListener(AUTH_REQUIRED_EVENT, handleAuthRequired);
    };
  }, [status]);

  const login = useCallback(async (request: LoginRequest) => {
    const response = await loginUser(request);
    setStoredAccessToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    setAuthRequiredMessage(null);
  }, []);

  const register = useCallback(
    async (request: RegisterRequest) => {
      await registerUser(request);
      await login({ email: request.email, password: request.password });
    },
    [login],
  );

  const logout = useCallback(() => {
    clearStoredAccessToken();
    setToken(null);
    setUser(null);
    setAuthRequiredMessage(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      status,
      isAuthenticated: Boolean(user && token),
      isLoading,
      authRequiredMessage,
      login,
      register,
      logout,
    }),
    [authRequiredMessage, isLoading, login, logout, register, status, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
