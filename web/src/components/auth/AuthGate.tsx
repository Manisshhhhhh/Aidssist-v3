import type { ReactNode } from "react";

import { useAuth } from "../../auth/useAuth";
import { AuthPage } from "../../pages/AuthPage";
import { Card } from "../ui/Card";

export function AuthGate({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, status } = useAuth();

  if (isLoading) {
    return (
      <Card className="mx-auto max-w-md text-center">
        <p className="font-semibold text-on-surface">Checking session</p>
        <p className="mt-2 text-sm text-on-surface-muted">Preparing your Aidssist workspace.</p>
      </Card>
    );
  }

  if (status?.user_auth_enabled && !isAuthenticated) {
    return <AuthPage />;
  }

  return <>{children}</>;
}
