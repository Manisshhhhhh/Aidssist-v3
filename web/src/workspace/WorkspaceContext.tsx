import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { createWorkspace as createWorkspaceRequest, listWorkspaces } from "../api/workspaces";
import { useAuth } from "../auth/useAuth";
import type { Workspace } from "../types/workspace";

const SELECTED_WORKSPACE_STORAGE_KEY = "aidssist_selected_workspace_id";

type WorkspaceContextValue = {
  workspaces: Workspace[];
  selectedWorkspace: Workspace | null;
  selectedWorkspaceId: number | null;
  isLoading: boolean;
  error: string | null;
  selectWorkspace: (workspaceId: number) => void;
  refreshWorkspaces: () => Promise<void>;
  createWorkspace: (name: string) => Promise<Workspace>;
};

export const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading: isAuthLoading, status, user } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<number | null>(() =>
    readStoredWorkspaceId(),
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shouldLoadWorkspaces = Boolean(
    status && (!status.user_auth_enabled || (status.user_auth_enabled && isAuthenticated)),
  );

  const refreshWorkspaces = useCallback(async () => {
    if (!shouldLoadWorkspaces) {
      setWorkspaces([]);
      setSelectedWorkspaceId(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const nextWorkspaces = await listWorkspaces();
      setWorkspaces(nextWorkspaces);
      setSelectedWorkspaceId((current) => {
        const currentStillExists = nextWorkspaces.some((workspace) => workspace.id === current);
        const nextId = currentStillExists ? current : nextWorkspaces[0]?.id ?? null;
        writeStoredWorkspaceId(nextId);
        return nextId;
      });
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load workspaces.");
    } finally {
      setIsLoading(false);
    }
  }, [shouldLoadWorkspaces]);

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    void refreshWorkspaces();
  }, [isAuthLoading, refreshWorkspaces, status?.user_auth_enabled, user?.id]);

  const selectWorkspace = useCallback((workspaceId: number) => {
    setSelectedWorkspaceId(workspaceId);
    writeStoredWorkspaceId(workspaceId);
  }, []);

  const createWorkspace = useCallback(
    async (name: string) => {
      const workspace = await createWorkspaceRequest({ name });
      await refreshWorkspaces();
      setSelectedWorkspaceId(workspace.id);
      writeStoredWorkspaceId(workspace.id);
      return workspace;
    },
    [refreshWorkspaces],
  );

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId) ?? null,
    [selectedWorkspaceId, workspaces],
  );

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      workspaces,
      selectedWorkspace,
      selectedWorkspaceId,
      isLoading,
      error,
      selectWorkspace,
      refreshWorkspaces,
      createWorkspace,
    }),
    [
      createWorkspace,
      error,
      isLoading,
      refreshWorkspaces,
      selectWorkspace,
      selectedWorkspace,
      selectedWorkspaceId,
      workspaces,
    ],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

function readStoredWorkspaceId(): number | null {
  if (typeof window === "undefined") {
    return null;
  }

  const value = window.localStorage.getItem(SELECTED_WORKSPACE_STORAGE_KEY);
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function writeStoredWorkspaceId(workspaceId: number | null): void {
  if (typeof window === "undefined") {
    return;
  }

  if (workspaceId) {
    window.localStorage.setItem(SELECTED_WORKSPACE_STORAGE_KEY, String(workspaceId));
  } else {
    window.localStorage.removeItem(SELECTED_WORKSPACE_STORAGE_KEY);
  }
}
