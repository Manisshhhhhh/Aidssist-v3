import { LogOut, UserCircle2 } from "lucide-react";

import { useAuth } from "../../auth/useAuth";
import { Button } from "../ui/Button";

export function UserMenu() {
  const { logout, status, user } = useAuth();

  if (!status?.user_auth_enabled || !user) {
    return null;
  }

  return (
    <div className="hidden items-center gap-2 rounded-xl border border-outline bg-surface2 px-3 py-2 sm:flex">
      <UserCircle2 size={17} className="text-primary-light" aria-hidden="true" />
      <div className="max-w-40 truncate text-xs text-on-surface-muted">{user.email}</div>
      <Button className="min-h-8 px-2 py-1 text-xs" onClick={logout} variant="ghost">
        <LogOut size={14} aria-hidden="true" />
        Logout
      </Button>
    </div>
  );
}
