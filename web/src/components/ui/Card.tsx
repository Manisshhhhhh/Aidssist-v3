import type { HTMLAttributes, ReactNode } from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function Card({ children, className, ...props }: CardProps) {
  return (
    <section
      className={twMerge(
        clsx(
          "surface-card rounded-2xl border border-outline bg-surface2/90 p-6 shadow-elevated backdrop-blur-sm",
          className,
        ),
      )}
      {...props}
    >
      {children}
    </section>
  );
}
