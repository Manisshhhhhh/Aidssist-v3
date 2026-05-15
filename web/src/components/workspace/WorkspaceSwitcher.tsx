import { useState } from "react";
import { BriefcaseBusiness, Loader2, Plus, RefreshCw } from "lucide-react";

import { useAuth } from "../../auth/useAuth";
import { useWorkspace } from "../../workspace/useWorkspace";
import { Button } from "../ui/Button";

export function WorkspaceSwitcher() {
  const { status } = useAuth();
  const {
    createWorkspace,
    error,
    isLoading,
    refreshWorkspaces,
    selectWorkspace,
    selectedWorkspace,
    selectedWorkspaceId,
    workspaces,
  } = useWorkspace();
  const [isCreating, setIsCreating] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");

  async function handleCreateWorkspace() {
    const trimmedName = newWorkspaceName.trim();
    if (!trimmedName) {
      return;
    }

    setIsCreating(true);
    try {
      await createWorkspace(trimmedName);
      setNewWorkspaceName("");
    } finally {
      setIsCreating(false);
    }
  }

  if (isLoading && workspaces.length === 0) {
    return (
      <div className="hidden items-center gap-2 rounded-xl border border-outline bg-surface2 px-3 py-2 text-xs text-on-surface-muted md:flex">
        <Loader2 className="animate-spin text-primary-light" size={14} aria-hidden="true" />
        Loading workspace
      </div>
    );
  }

  return (
    <div className="hidden min-w-0 items-center gap-2 md:flex">
      <label className="sr-only" htmlFor="workspace-select">
        Workspace
      </label>
      <div className="flex min-w-0 items-center gap-2 rounded-xl border border-outline bg-surface2 px-3 py-2">
        <BriefcaseBusiness className="shrink-0 text-primary-light" size={15} aria-hidden="true" />
        {workspaces.length > 1 ? (
          <select
            className="min-w-0 max-w-52 bg-transparent text-xs font-semibold text-on-surface outline-none"
            id="workspace-select"
            onChange={(event) => selectWorkspace(Number(event.target.value))}
            value={selectedWorkspaceId ?? ""}
          >
            {workspaces.map((workspace) => (
              <option className="bg-surface1 text-on-surface" key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        ) : (
          <span className="max-w-48 truncate text-xs font-semibold text-on-surface">
            {selectedWorkspace?.name ?? "Default Workspace"}
          </span>
        )}
      </div>

      {status?.user_auth_enabled ? (
        <form
          className="hidden items-center gap-2 xl:flex"
          onSubmit={(event) => {
            event.preventDefault();
            void handleCreateWorkspace();
          }}
        >
          <label className="sr-only" htmlFor="workspace-name">
            New workspace name
          </label>
          <input
            className="h-9 w-40 rounded-xl border border-outline bg-surface2 px-3 text-xs text-on-surface outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/25"
            id="workspace-name"
            maxLength={80}
            onChange={(event) => setNewWorkspaceName(event.target.value)}
            placeholder="New workspace"
            value={newWorkspaceName}
          />
          <Button
            aria-label="Create workspace"
            className="min-h-9 px-3 py-1"
            disabled={isCreating || newWorkspaceName.trim().length === 0}
            type="submit"
            variant="secondary"
          >
            {isCreating ? (
              <Loader2 className="animate-spin" size={15} aria-hidden="true" />
            ) : (
              <Plus size={15} aria-hidden="true" />
            )}
          </Button>
        </form>
      ) : null}

      {error ? (
        <Button
          aria-label="Retry workspace loading"
          className="min-h-9 px-3 py-1 text-danger"
          onClick={() => void refreshWorkspaces()}
          variant="ghost"
        >
          <RefreshCw size={15} aria-hidden="true" />
        </Button>
      ) : null}
    </div>
  );
}
