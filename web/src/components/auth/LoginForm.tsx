import { useState, type FormEvent } from "react";
import { AlertCircle, LogIn } from "lucide-react";

import { useAuth } from "../../auth/useAuth";
import { Button } from "../ui/Button";

type LoginFormProps = {
  onShowRegister: () => void;
};

export function LoginForm({ onShowRegister }: LoginFormProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
      <label className="block text-sm font-medium text-on-surface">
        Email
        <input
          autoComplete="email"
          className="mt-2 w-full rounded-xl border border-outline bg-surface1 px-4 py-3 text-on-surface outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          onChange={(event) => setEmail(event.target.value)}
          required
          type="email"
          value={email}
        />
      </label>
      <label className="block text-sm font-medium text-on-surface">
        Password
        <input
          autoComplete="current-password"
          className="mt-2 w-full rounded-xl border border-outline bg-surface1 px-4 py-3 text-on-surface outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>
      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-danger/25 bg-danger/10 p-3 text-sm text-on-surface">
          <AlertCircle className="mt-0.5 shrink-0 text-danger" size={17} aria-hidden="true" />
          <p>{error}</p>
        </div>
      ) : null}
      <Button className="w-full" disabled={isSubmitting} type="submit">
        <LogIn size={17} aria-hidden="true" />
        Sign in
      </Button>
      <button
        className="w-full text-sm font-medium text-primary-light hover:text-primary"
        onClick={onShowRegister}
        type="button"
      >
        Create an account
      </button>
    </form>
  );
}
