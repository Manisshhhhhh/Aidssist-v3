import type { ReactNode } from "react";

import { BrandMark } from "../brand/BrandMark";
import { UserMenu } from "../auth/UserMenu";
import { ApiStatusBadge } from "./ApiStatusBadge";
import { ThemeToggle } from "./ThemeToggle";
import { WorkspaceSwitcher } from "../workspace/WorkspaceSwitcher";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-on-background">
      <div className="ambient-glow pointer-events-none fixed inset-0 opacity-70" />
      <div className="ambient-grid pointer-events-none fixed inset-0 opacity-70" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
        <header className="animate-reveal-up sticky top-5 z-20 flex items-center justify-between gap-4 rounded-2xl border border-outline bg-surface1/95 px-4 py-3 shadow-panel backdrop-blur-xl">
          <div className="flex min-w-0 items-center gap-3">
            <div className="soft-icon flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-primary/25 bg-primary/10 text-primary-light shadow-inner">
              <BrandMark size={30} variant="duo" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-primary-light">Aidssist V3</p>
              <p className="truncate text-xs text-on-surface-muted">Autonomous data intelligence</p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <WorkspaceSwitcher />
            <UserMenu />
            <ApiStatusBadge />
            <ThemeToggle />
          </div>
        </header>

        <main className="flex flex-1 items-center py-10 sm:py-14">{children}</main>

        <footer className="pb-2 text-center text-xs text-on-surface-disabled">
          Aidssist V3 foundation build · frontend shell
        </footer>
      </div>
    </div>
  );
}
