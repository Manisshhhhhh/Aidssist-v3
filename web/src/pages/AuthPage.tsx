import { useState } from "react";
import { ShieldCheck } from "lucide-react";

import { BrandMark } from "../components/brand/BrandMark";
import { LoginForm } from "../components/auth/LoginForm";
import { RegisterForm } from "../components/auth/RegisterForm";
import { Card } from "../components/ui/Card";

export function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("login");

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-center">
      <div>
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl border border-primary/25 bg-primary/10 text-primary-light shadow-panel">
          <BrandMark size={42} variant="duo" />
        </div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary-light">
          Secure workspace
        </p>
        <h1 className="mt-4 max-w-2xl text-4xl font-semibold leading-tight text-on-surface sm:text-5xl">
          Sign in to your Aidssist intelligence workspace.
        </h1>
        <p className="mt-5 max-w-xl text-base leading-7 text-on-surface-muted">
          User authentication is enabled on this server. Your datasets and generated artifacts are
          scoped to your account.
        </p>
      </div>

      <Card>
        <div className="mb-6 flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light">
            <ShieldCheck size={21} aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-on-surface">
              {mode === "login" ? "Welcome back" : "Create account"}
            </h2>
            <p className="mt-1 text-sm text-on-surface-muted">
              {mode === "login" ? "Use your Aidssist credentials." : "Start with a local Aidssist account."}
            </p>
          </div>
        </div>

        {mode === "login" ? (
          <LoginForm onShowRegister={() => setMode("register")} />
        ) : (
          <RegisterForm onShowLogin={() => setMode("login")} />
        )}
      </Card>
    </div>
  );
}
