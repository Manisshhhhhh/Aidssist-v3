import { apiRequest } from "./client";
import type { DatasetDeleteResponse, DatasetMetadata, DatasetUpdateRequest } from "../types/dataset";

export function uploadDataset(file: File, workspaceId?: number | null): Promise<DatasetMetadata> {
  const formData = new FormData();
  formData.append("file", file);
  const query = workspaceId ? `?workspace_id=${encodeURIComponent(String(workspaceId))}` : "";

  return apiRequest<DatasetMetadata>(`/upload${query}`, {
    method: "POST",
    body: formData,
  });
}

export function listDatasets(workspaceId?: number | null): Promise<DatasetMetadata[]> {
  const query = workspaceId ? `?workspace_id=${encodeURIComponent(String(workspaceId))}` : "";
  return apiRequest<DatasetMetadata[]>(`/datasets${query}`);
}

export function getDataset(datasetId: string): Promise<DatasetMetadata> {
  return apiRequest<DatasetMetadata>(`/datasets/${encodeURIComponent(datasetId)}`);
}

export function deleteDataset(datasetId: string): Promise<DatasetDeleteResponse> {
  return apiRequest<DatasetDeleteResponse>(`/datasets/${encodeURIComponent(datasetId)}`, {
    method: "DELETE",
  });
}

export function renameDataset(datasetId: string, request: DatasetUpdateRequest): Promise<DatasetMetadata> {
  return apiRequest<DatasetMetadata>(`/datasets/${encodeURIComponent(datasetId)}`, {
    method: "PATCH",
    body: { ...request },
  });
}
