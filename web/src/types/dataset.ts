export interface DatasetMetadata {
  dataset_id: string;
  original_filename: string;
  stored_filename: string;
  file_size_bytes: number;
  content_type: string | null;
  created_at: string;
  workspace_id?: number | null;
  row_count?: number | null;
  column_count?: number | null;
  columns?: string[] | null;
  last_analyzed_at?: string | null;
}

export interface DatasetDeleteResponse {
  dataset_id: string;
  deleted: boolean;
  message: string;
}

export interface DatasetUpdateRequest {
  original_filename: string;
}
