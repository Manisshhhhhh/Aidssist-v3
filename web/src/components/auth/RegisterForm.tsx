import { useState, type FormEvent } from "react";
import { AlertCircle, UserPlus } from "lucide-react";

import { useAuth } from "../../auth/useAuth";
import { Button } from "../ui/Button";

type RegisterFormProps = {
  onShowLogin: () => void;
};

export function RegisterForm({ onShowLogin }: RegisterFormProps) {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ email, password, full_name: fullName });
    } catch (registerError) {
      setError(registerError instanceof Error ? registerError.message : "Unable to create account.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
      <label className="block text-sm font-medium text-on-surface">
        Full name
        <input
          autoComplete="name"
          className="mt-2 w-full rounded-xl border border-outline bg-surface1 px-4 py-3 text-on-surface outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          onChange={(event) => setFullName(event.target.value)}
          required
          type="text"
          value={fullName}
        />
      </label>
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
          autoComplete="new-password"
          className="mt-2 w-full rounded-xl border border-outline bg-surface1 px-4 py-3 text-on-surface outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
          minLength={8}
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
        <UserPlus size={17} aria-hidden="true" />
        Create account
      </Button>
      <button
        className="w-full text-sm font-medium text-primary-light hover:text-primary"
        onClick={onShowLogin}
        type="button"
      >
        Sign in instead
      </button>
    </form>
  );
}
