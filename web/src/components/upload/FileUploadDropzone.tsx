import { useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileUp, Loader2, UploadCloud } from "lucide-react";

import { uploadDataset } from "../../api/datasets";
import type { DatasetMetadata } from "../../types/dataset";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

type FileUploadDropzoneProps = {
  onUploadSuccess: (dataset: DatasetMetadata) => void;
  workspaceId?: number | null;
};

export function FileUploadDropzone({ onUploadSuccess, workspaceId }: FileUploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function handleFile(file: File | undefined) {
    setSuccessMessage(null);
    setError(null);

    if (!file) {
      return;
    }

    if (!isSupportedDatasetFile(file)) {
      setSelectedFile(null);
      setError("Upload a CSV or Excel .xlsx file.");
      return;
    }

    setSelectedFile(file);
  }

  async function handleUpload() {
    if (!selectedFile) {
      setError("Choose a CSV or Excel .xlsx file before uploading.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const dataset = await uploadDataset(selectedFile, workspaceId);
      setSuccessMessage(`${dataset.original_filename} uploaded successfully.`);
      onUploadSuccess(dataset);
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (uploadError) {
      setError(getUploadErrorMessage(uploadError));
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <Card>
      <div
        className={[
          "group/dropzone flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed p-6 text-center transition duration-300 motion-safe:hover:-translate-y-0.5",
          isDragging
            ? "border-primary/80 bg-primary/10 shadow-glow"
            : "border-outline bg-surface1 hover:border-primary/45 hover:bg-surface3",
        ].join(" ")}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDragOver={(event) => {
          event.preventDefault();
        }}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          aria-label="Choose CSV dataset file"
          accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          className="sr-only"
          onChange={(event) => handleFile(event.target.files?.[0])}
          ref={inputRef}
          type="file"
        />

        <div className="soft-icon flex h-14 w-14 items-center justify-center rounded-2xl border border-primary/25 bg-primary/10 text-primary-light transition duration-300 group-hover/dropzone:scale-105">
          <UploadCloud size={26} aria-hidden="true" />
        </div>
        <h2 className="mt-5 text-xl font-semibold text-on-surface">Upload a CSV or Excel dataset</h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-on-surface-muted">
          Select or drop one CSV or Excel .xlsx file. Excel sheets are converted to Aidssist's
          canonical CSV format for analysis.
        </p>

        <div className="mt-6 flex flex-col items-center gap-3 sm:flex-row">
          <Button
            onClick={() => inputRef.current?.click()}
            variant="secondary"
            disabled={isUploading}
          >
            <FileUp size={18} aria-hidden="true" />
            Choose file
          </Button>
          <Button onClick={handleUpload} disabled={!selectedFile || isUploading}>
            {isUploading ? (
              <>
                <Loader2 className="animate-spin" size={18} aria-hidden="true" />
                Uploading
              </>
            ) : (
              "Upload Dataset"
            )}
          </Button>
        </div>

        {selectedFile ? (
          <div className="animate-reveal-up mt-5 rounded-xl border border-outline bg-surface2 px-4 py-3 text-left text-sm text-on-surface">
            <p className="font-medium text-on-surface">{selectedFile.name}</p>
            <p className="mt-1 text-xs text-on-surface-muted">{formatFileSize(selectedFile.size)}</p>
          </div>
        ) : null}
      </div>

      {error ? (
        <p className="animate-reveal-up mt-4 flex items-start gap-2 rounded-xl border border-danger/25 bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 shrink-0" size={16} aria-hidden="true" />
          {error}
        </p>
      ) : null}

      {successMessage ? (
        <p className="animate-reveal-up mt-4 flex items-start gap-2 rounded-xl border border-success/25 bg-success/10 px-4 py-3 text-sm text-success">
          <CheckCircle2 className="mt-0.5 shrink-0" size={16} aria-hidden="true" />
          {successMessage}
        </p>
      ) : null}
    </Card>
  );
}

function isSupportedDatasetFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return name.endsWith(".csv") || name.endsWith(".xlsx");
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getUploadErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Upload failed. Try again with a valid CSV or Excel .xlsx file.";
}
