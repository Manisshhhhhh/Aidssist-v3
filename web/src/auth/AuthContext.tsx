import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { getAuthStatus, getCurrentUser, loginUser, registerUser } from "../api/auth";
import { clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken } from "../api/client";
import type { AuthStatusResponse, AuthUser, LoginRequest, RegisterRequest } from "../types/auth";

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  status: AuthStatusResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
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

  const login = useCallback(async (request: LoginRequest) => {
    const response = await loginUser(request);
    setStoredAccessToken(response.access_token);
    setToken(response.access_token);
    setUser(response.user);
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
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      status,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      register,
      logout,
    }),
    [isLoading, login, logout, register, status, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
