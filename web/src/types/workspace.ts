export type WorkspaceRole = "owner" | "admin" | "editor" | "viewer";

export interface Workspace {
  id: number;
  name: string;
  slug: string;
  owner_user_id?: number | null;
  current_user_role?: WorkspaceRole | null;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreateRequest {
  name: string;
}

export interface WorkspaceMember {
  user_id: number;
  email: string;
  full_name: string;
  role: WorkspaceRole;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMemberUpsertRequest {
  email: string;
  role: WorkspaceRole;
}
