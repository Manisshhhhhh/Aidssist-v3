from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import init_db
from app.models.analysis_models import AnalysisResult
from app.models.dataset_models import DatasetMetadata
from app.models.forecast_models import ForecastResponse
from app.models.report_models import ReportResponse
from app.repositories.analysis_repository import upsert_analysis
from app.repositories.dataset_repository import upsert_dataset
from app.repositories.forecast_repository import create_forecast_record
from app.repositories.report_repository import create_report_record
from app.services import storage_service
from app.services.artifact_service import record_path_artifact


def main() -> int:
    summary = sync_filesystem_to_db()
    print(
        "Filesystem sync complete: "
        f"datasets={summary['datasets']}, "
        f"analyses={summary['analyses']}, "
        f"forecasts={summary['forecasts']}, "
        f"reports={summary['reports']}, "
        f"skipped={summary['skipped']}"
    )
    return 0


def sync_filesystem_to_db() -> dict[str, int]:
    init_db()
    counts = {"datasets": 0, "analyses": 0, "forecasts": 0, "reports": 0, "skipped": 0}
    datasets_dir = storage_service.ensure_datasets_dir()

    for metadata_path in sorted(datasets_dir.glob(f"*/{storage_service.METADATA_FILENAME}")):
        dataset_dir = metadata_path.parent
        try:
            metadata = DatasetMetadata.model_validate(load_json(metadata_path))
            upsert_dataset(
                metadata,
                storage_path=dataset_dir / storage_service.ORIGINAL_FILENAME,
                metadata_path=metadata_path,
            )
            record_path_artifact(
                artifact_type="original_csv",
                storage_key=storage_service.get_original_key(metadata.dataset_id),
                filename=storage_service.ORIGINAL_FILENAME,
                dataset_id=metadata.dataset_id,
                workspace_id=metadata.workspace_id,
                content_type="text/csv",
            )
            record_path_artifact(
                artifact_type="metadata_json",
                storage_key=storage_service.get_metadata_key(metadata.dataset_id),
                filename=storage_service.METADATA_FILENAME,
                dataset_id=metadata.dataset_id,
                workspace_id=metadata.workspace_id,
                content_type="application/json",
            )
            counts["datasets"] += 1
        except Exception:
            counts["skipped"] += 1
            continue

        analysis_path = dataset_dir / storage_service.ANALYSIS_FILENAME
        if analysis_path.is_file():
            try:
                upsert_analysis(AnalysisResult.model_validate(load_json(analysis_path)), analysis_path)
                record_path_artifact(
                    artifact_type="analysis_json",
                    storage_key=storage_service.get_analysis_key(metadata.dataset_id),
                    filename=storage_service.ANALYSIS_FILENAME,
                    dataset_id=metadata.dataset_id,
                    workspace_id=metadata.workspace_id,
                    content_type="application/json",
                )
                counts["analyses"] += 1
            except Exception:
                counts["skipped"] += 1

        for forecast_path in sorted(dataset_dir.glob("forecast_*.json")):
            try:
                create_forecast_record(ForecastResponse.model_validate(load_json(forecast_path)), forecast_path)
                record_path_artifact(
                    artifact_type="forecast_json",
                    storage_key=storage_service.get_forecast_key(metadata.dataset_id, forecast_path.name),
                    filename=forecast_path.name,
                    dataset_id=metadata.dataset_id,
                    workspace_id=metadata.workspace_id,
                    content_type="application/json",
                )
                counts["forecasts"] += 1
            except Exception:
                counts["skipped"] += 1

        reports_dir = dataset_dir / "reports"
        if reports_dir.is_dir():
            for report_dir in sorted(path for path in reports_dir.iterdir() if path.is_dir()):
                try:
                    report_response = build_report_response(metadata.dataset_id, report_dir)
                    create_report_record(
                        report_response,
                        report_path=report_dir / "report.html",
                        json_path=report_dir / "report.json",
                    )
                    if (report_dir / "report.html").is_file():
                        record_path_artifact(
                            artifact_type="report_html",
                            storage_key=storage_service.get_report_key(metadata.dataset_id, report_dir.name, "report.html"),
                            filename="report.html",
                            dataset_id=metadata.dataset_id,
                            workspace_id=metadata.workspace_id,
                            content_type="text/html",
                            metadata={"report_id": report_dir.name},
                        )
                    if (report_dir / "report.json").is_file():
                        record_path_artifact(
                            artifact_type="report_json",
                            storage_key=storage_service.get_report_key(metadata.dataset_id, report_dir.name, "report.json"),
                            filename="report.json",
                            dataset_id=metadata.dataset_id,
                            workspace_id=metadata.workspace_id,
                            content_type="application/json",
                            metadata={"report_id": report_dir.name},
                        )
                    counts["reports"] += 1
                except Exception:
                    counts["skipped"] += 1

    return counts


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_report_response(dataset_id: str, report_dir: Path) -> ReportResponse:
    manifest_path = report_dir / "manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    report_format = manifest.get("format") if manifest.get("format") in {"html", "json"} else "html"
    created_at = parse_datetime(manifest.get("created_at")) or datetime.fromtimestamp(report_dir.stat().st_mtime, timezone.utc)
    report_id = report_dir.name
    return ReportResponse(
        dataset_id=dataset_id,
        report_id=report_id,
        format=report_format,
        filename=f"aidssist_report_{dataset_id[:12]}.{report_format}",
        download_url=f"/datasets/{dataset_id}/reports/{report_id}/download",
        created_at=created_at,
    )


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


if __name__ == "__main__":
    sys.exit(main())
