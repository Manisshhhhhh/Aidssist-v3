import type { ReactNode } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CalendarClock,
  Database,
  FileDigit,
  Pencil,
  RefreshCw,
  Rows3,
  Search,
  Trash2,
  X,
} from "lucide-react";

import { deleteDataset, listDatasets, renameDataset } from "../../api/datasets";
import { getFriendlyApiErrorMessage } from "../../api/errors";
import type { DatasetMetadata } from "../../types/dataset";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type DatasetListProps = {
  onDatasetSelect: (dataset: DatasetMetadata) => void;
  refreshSignal?: number;
  selectedDatasetId?: string | null;
  workspaceId?: number | null;
};

export function DatasetList({
  onDatasetSelect,
  refreshSignal = 0,
  selectedDatasetId,
  workspaceId,
}: DatasetListProps) {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);
  const [editingDatasetId, setEditingDatasetId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const filteredDatasets = useMemo(() => {
    const normalized = searchTerm.trim().toLowerCase();
    if (!normalized) {
      return datasets;
    }

    return datasets.filter((dataset) => {
      const haystack = [
        dataset.original_filename,
        dataset.dataset_id,
        ...(dataset.columns ?? []),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [datasets, searchTerm]);

  const loadDatasets = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      setDatasets(await listDatasets(workspaceId));
    } catch (loadError) {
      setError(getLoadErrorMessage(loadError));
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadDatasets();
  }, [loadDatasets, refreshSignal]);

  async function handleDelete(dataset: DatasetMetadata) {
    const confirmed = window.confirm(
      `Delete "${dataset.original_filename}"?\n\nThis removes the local dataset, analysis, forecasts, charts, and reports for this upload.`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingDatasetId(dataset.dataset_id);
    setError(null);

    try {
      await deleteDataset(dataset.dataset_id);
      setDatasets((current) =>
        current.filter((item) => item.dataset_id !== dataset.dataset_id),
      );
    } catch (deleteError) {
      setError(getDeleteErrorMessage(deleteError));
    } finally {
      setDeletingDatasetId(null);
    }
  }

  function startRename(dataset: DatasetMetadata) {
    setEditingDatasetId(dataset.dataset_id);
    setRenameValue(dataset.original_filename);
    setError(null);
  }

  async function handleRename(dataset: DatasetMetadata) {
    const nextName = renameValue.trim();
    if (!nextName || nextName === dataset.original_filename || isRenaming) {
      setEditingDatasetId(null);
      return;
    }

    setIsRenaming(true);
    setError(null);
    try {
      const updated = await renameDataset(dataset.dataset_id, { original_filename: nextName });
      setDatasets((current) =>
        current.map((item) => (item.dataset_id === updated.dataset_id ? updated : item)),
      );
      setEditingDatasetId(null);
    } catch (renameError) {
      setError(getRenameErrorMessage(renameError));
    } finally {
      setIsRenaming(false);
    }
  }

  return (
    <Card className="h-full">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary-light">
            Recent datasets
          </p>
          <h2 className="mt-2 text-xl font-semibold text-on-surface">Dataset registry</h2>
        </div>
        <Button
          aria-label="Refresh datasets"
          className="min-h-10 px-3"
          disabled={isLoading}
          onClick={() => void loadDatasets()}
          variant="ghost"
        >
          <RefreshCw className={isLoading ? "animate-spin" : ""} size={17} aria-hidden="true" />
        </Button>
      </div>

      <label className="mt-5 flex items-center gap-2 rounded-xl border border-outline bg-surface1 px-3 py-2 text-sm text-on-surface">
        <Search className="shrink-0 text-on-surface-muted" size={16} aria-hidden="true" />
        <input
          className="min-h-9 flex-1 bg-transparent outline-none placeholder:text-on-surface-disabled"
          onChange={(event) => setSearchTerm(event.target.value)}
          placeholder="Search datasets or columns"
          type="search"
          value={searchTerm}
        />
      </label>

      <div className="mt-5">
        {isLoading ? <DatasetListSkeleton /> : null}

        {!isLoading && error ? (
          <div className="rounded-xl border border-danger/25 bg-danger/10 p-4 text-sm text-danger">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 shrink-0" size={16} aria-hidden="true" />
              <p>{error}</p>
            </div>
          </div>
        ) : null}

        {!isLoading && !error && datasets.length === 0 ? (
          <div className="rounded-xl border border-outline bg-surface1 p-5 text-sm text-on-surface-muted">
            No datasets uploaded yet. Add a CSV to begin.
          </div>
        ) : null}

        {!isLoading && !error && datasets.length > 0 && filteredDatasets.length === 0 ? (
          <div className="rounded-xl border border-outline bg-surface1 p-5 text-sm text-on-surface-muted">
            No datasets match this search.
          </div>
        ) : null}

        {!isLoading && !error && filteredDatasets.length > 0 ? (
          <div className="space-y-3">
            {filteredDatasets.map((dataset) => (
              <article
                className={[
                  "w-full rounded-xl border p-4 text-left transition duration-200 motion-safe:hover:-translate-y-0.5",
                  selectedDatasetId === dataset.dataset_id
                    ? "border-primary/60 bg-primary/10"
                    : "border-outline bg-surface1 hover:border-primary/35 hover:bg-surface3",
                ].join(" ")}
                key={dataset.dataset_id}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    {editingDatasetId === dataset.dataset_id ? (
                      <form
                        className="flex gap-2"
                        onSubmit={(event) => {
                          event.preventDefault();
                          void handleRename(dataset);
                        }}
                      >
                        <input
                          aria-label={`Rename ${dataset.original_filename}`}
                          className="min-h-9 min-w-0 rounded-lg border border-outline bg-surface2 px-3 py-1 text-sm text-on-surface outline-none focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
                          disabled={isRenaming}
                          onChange={(event) => setRenameValue(event.target.value)}
                          value={renameValue}
                        />
                        <Button className="min-h-9 px-3" disabled={isRenaming} type="submit">
                          Save
                        </Button>
                        <Button
                          aria-label="Cancel rename"
                          className="min-h-9 px-3"
                          disabled={isRenaming}
                          onClick={() => setEditingDatasetId(null)}
                          type="button"
                          variant="ghost"
                        >
                          <X size={15} aria-hidden="true" />
                        </Button>
                      </form>
                    ) : (
                      <p className="truncate text-sm font-semibold text-on-surface">
                        {dataset.original_filename}
                      </p>
                    )}
                    <p className="mt-1 font-mono text-xs text-primary-light">
                      {shortDatasetId(dataset.dataset_id)}
                    </p>
                  </div>
                  <span className="rounded-full border border-outline bg-surface2 px-2.5 py-1 text-xs text-on-surface-muted">
                    CSV
                  </span>
                </div>

                <div className="mt-4 grid gap-2 text-xs text-on-surface-muted sm:grid-cols-2">
                  <DatasetMetaItem
                    icon={<Rows3 size={14} aria-hidden="true" />}
                    label={`${formatNullableNumber(dataset.row_count)} rows`}
                  />
                  <DatasetMetaItem
                    icon={<Database size={14} aria-hidden="true" />}
                    label={`${formatNullableNumber(dataset.column_count)} columns`}
                  />
                  <DatasetMetaItem
                    icon={<CalendarClock size={14} aria-hidden="true" />}
                    label={`Uploaded ${formatDate(dataset.created_at)}`}
                  />
                  <DatasetMetaItem
                    icon={<CalendarClock size={14} aria-hidden="true" />}
                    label={`Analyzed ${formatOptionalDate(dataset.last_analyzed_at)}`}
                  />
                  <DatasetMetaItem
                    icon={<FileDigit size={14} aria-hidden="true" />}
                    label={formatFileSize(dataset.file_size_bytes)}
                  />
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    aria-label={`Open dataset ${dataset.original_filename}`}
                    className="min-h-10 px-3"
                    onClick={() => onDatasetSelect(dataset)}
                    variant="secondary"
                  >
                    Open dataset
                  </Button>
                  <Button
                    aria-label={`Rename dataset ${dataset.original_filename}`}
                    className="min-h-10 px-3"
                    disabled={editingDatasetId === dataset.dataset_id}
                    onClick={() => startRename(dataset)}
                    variant="ghost"
                  >
                    <Pencil size={16} aria-hidden="true" />
                    Rename
                  </Button>
                  <Button
                    aria-label={`Delete dataset ${dataset.original_filename}`}
                    className="min-h-10 px-3 text-danger hover:border-danger/40 hover:bg-danger/10 hover:text-danger"
                    disabled={deletingDatasetId === dataset.dataset_id}
                    onClick={() => void handleDelete(dataset)}
                    variant="ghost"
                  >
                    <Trash2 size={16} aria-hidden="true" />
                    {deletingDatasetId === dataset.dataset_id ? "Deleting" : "Delete"}
                  </Button>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function DatasetMetaItem({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="flex min-w-0 items-center gap-2 rounded-lg bg-surface2 px-2.5 py-2">
      <span className="shrink-0 text-primary-light">{icon}</span>
      <span className="truncate">{label}</span>
    </span>
  );
}

function DatasetListSkeleton() {
  return (
    <div className="space-y-3">
      {[0, 1, 2].map((item) => (
        <div
          className="shimmer h-24 rounded-xl border border-outline bg-surface1"
          key={item}
        />
      ))}
    </div>
  );
}

function shortDatasetId(datasetId: string): string {
  return datasetId.length > 12 ? `${datasetId.slice(0, 8)}...${datasetId.slice(-4)}` : datasetId;
}

function formatNullableNumber(value: number | null | undefined): string {
  return typeof value === "number" ? value.toLocaleString() : "unknown";
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "unknown date";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatOptionalDate(value: string | null | undefined): string {
  return value ? formatDate(value) : "not yet";
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getLoadErrorMessage(error: unknown): string {
  return getFriendlyApiErrorMessage(error, { fallback: "Unable to load datasets." });
}

function getDeleteErrorMessage(error: unknown): string {
  return getFriendlyApiErrorMessage(error, { fallback: "Unable to delete this dataset." });
}

function getRenameErrorMessage(error: unknown): string {
  return getFriendlyApiErrorMessage(error, { fallback: "Unable to rename this dataset." });
}
