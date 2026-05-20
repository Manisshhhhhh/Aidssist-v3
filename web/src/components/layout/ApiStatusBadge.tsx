import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, ShieldAlert, WifiOff } from "lucide-react";

import { API_BASE_URL, ApiClientError, apiRequest } from "../../api/client";
import type { HealthResponse } from "../../types/api";

type ApiStatus = "checking" | "online" | "restricted" | "offline";

export function ApiStatusBadge() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    let isMounted = true;

    async function checkApi(showChecking = false) {
      if (showChecking) {
        setStatus("checking");
      }

      try {
        await apiRequest<HealthResponse>("/health");
        if (isMounted) {
          setStatus("online");
        }
      } catch (error) {
        if (isMounted) {
          setStatus(
            error instanceof ApiClientError && error.status === 401 ? "restricted" : "offline",
          );
        }
      }
    }

    void checkApi(true);
    const intervalId = window.setInterval(() => {
      void checkApi(false);
    }, 5000);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const statusConfig = {
    checking: {
      label: "Checking API",
      icon: <Loader2 className="animate-spin" size={13} aria-hidden="true" />,
      className: "border-outline bg-surface2 text-on-surface-muted",
    },
    online: {
      label: "API Online",
      icon: <CheckCircle2 size={13} aria-hidden="true" />,
      className: "border-success/30 bg-success/10 text-success",
    },
    restricted: {
      label: "Auth Required",
      icon: <ShieldAlert size={13} aria-hidden="true" />,
      className: "border-warning/30 bg-warning/10 text-on-surface",
    },
    offline: {
      label: "API Offline",
      icon: <WifiOff size={13} aria-hidden="true" />,
      className: "border-danger/30 bg-danger/10 text-danger",
    },
  } satisfies Record<ApiStatus, { label: string; icon: ReactNode; className: string }>;

  const current = statusConfig[status];

  return (
    <button
      aria-label={`API status: ${current.label}. Using ${API_BASE_URL}. Click to recheck.`}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold transition hover:bg-surface3 focus:outline-none focus:ring-2 focus:ring-primary/35 ${current.className}`}
      onClick={() => {
        setStatus("checking");
        void apiRequest<HealthResponse>("/health")
          .then(() => setStatus("online"))
          .catch((error) =>
            setStatus(
              error instanceof ApiClientError && error.status === 401 ? "restricted" : "offline",
            ),
          );
      }}
      title={`API: ${API_BASE_URL}`}
      type="button"
    >
      {current.icon}
      {current.label}
    </button>
  );
}
