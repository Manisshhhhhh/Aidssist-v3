import { FileSpreadsheet, Link2, LockKeyhole, PlugZap } from "lucide-react";

import { Card } from "../ui/Card";

const sources = [
  {
    name: "Excel",
    status: "Available",
    description: "Import .xlsx files directly through the upload area. The first worksheet is converted to CSV for analysis.",
    icon: FileSpreadsheet,
    active: true,
  },
  {
    name: "Power BI",
    status: "Connector setup required",
    description: "Direct import requires Microsoft OAuth, workspace permissions, and dataset export configuration.",
    icon: PlugZap,
    active: false,
  },
  {
    name: "Tableau",
    status: "Connector setup required",
    description: "Direct import requires Tableau REST API credentials and site/project access.",
    icon: PlugZap,
    active: false,
  },
  {
    name: "Aidssist Link",
    status: "Connector setup required",
    description: "Use this future connector to let external software push datasets into Aidssist through a secure API key.",
    icon: Link2,
    active: false,
  },
];

export function DataSourceConnectPanel() {
  return (
    <Card>
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
          Data sources
        </p>
        <h2 className="mt-2 text-xl font-semibold text-on-surface">Import and connector options</h2>
        <p className="mt-2 text-sm leading-6 text-on-surface-muted">
          Excel import is available now. Power BI, Tableau, and Aidssist Link are shown as
          connector targets and require credentials before direct import can be enabled.
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {sources.map((source) => {
          const Icon = source.icon;

          return (
            <div
              className={`rounded-xl border p-4 ${
                source.active
                  ? "border-success/30 bg-success/10"
                  : "border-outline bg-surface1"
              }`}
              key={source.name}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${
                    source.active
                      ? "border-success/30 bg-success/10 text-success"
                      : "border-outline bg-surface2 text-on-surface-muted"
                  }`}
                >
                  <Icon size={18} aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold text-on-surface">{source.name}</h3>
                    {!source.active ? <LockKeyhole size={14} className="text-warning" aria-hidden="true" /> : null}
                  </div>
                  <p className={source.active ? "mt-1 text-xs text-success" : "mt-1 text-xs text-warning"}>
                    {source.status}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-on-surface-muted">{source.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
