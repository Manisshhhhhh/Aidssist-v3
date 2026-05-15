import { apiRequest } from "./client";
import type {
  Workspace,
  WorkspaceCreateRequest,
  WorkspaceMember,
  WorkspaceMemberUpsertRequest,
  WorkspaceRole,
} from "../types/workspace";

export function listWorkspaces(): Promise<Workspace[]> {
  return apiRequest<Workspace[]>("/workspaces");
}

export function createWorkspace(request: WorkspaceCreateRequest): Promise<Workspace> {
  return apiRequest<Workspace>("/workspaces", {
    method: "POST",
    body: { ...request },
  });
}

export function listWorkspaceMembers(workspaceId: number): Promise<WorkspaceMember[]> {
  return apiRequest<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`);
}

export function addWorkspaceMember(
  workspaceId: number,
  request: WorkspaceMemberUpsertRequest,
): Promise<WorkspaceMember> {
  return apiRequest<WorkspaceMember>(`/workspaces/${workspaceId}/members`, {
    method: "POST",
    body: { ...request },
  });
}

export function updateWorkspaceMemberRole(
  workspaceId: number,
  userId: number,
  role: WorkspaceRole,
): Promise<WorkspaceMember> {
  return apiRequest<WorkspaceMember>(`/workspaces/${workspaceId}/members/${userId}`, {
    method: "PATCH",
    body: { role },
  });
}
