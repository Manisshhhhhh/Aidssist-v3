import type { ButtonHTMLAttributes, ReactNode } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-primary/70 bg-primary text-background shadow-glow hover:border-primary-light hover:bg-primary-light",
  secondary:
    "border-outline bg-transparent text-on-surface hover:border-primary/45 hover:bg-surface3",
  ghost:
    "border-transparent bg-transparent text-on-surface-muted hover:bg-surface2 hover:text-on-surface",
};

export function Button({
  children,
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={twMerge(
        clsx(
          "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition duration-200 focus:outline-none focus:ring-2 focus:ring-primary/45 active:translate-y-px disabled:cursor-not-allowed disabled:opacity-55 motion-safe:hover:-translate-y-0.5",
          variantClasses[variant],
          className,
        ),
      )}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}
