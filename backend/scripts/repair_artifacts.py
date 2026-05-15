from __future__ import annotations

import argparse
from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import init_db
from app.repositories import artifact_repository
from app.services import storage_service
from app.services.artifact_service import audit_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and optionally repair Aidssist artifact records.")
    parser.add_argument("--create-missing-records", action="store_true", help="Create placeholder records for orphan files.")
    parser.add_argument("--soft-delete-missing-files", action="store_true", help="Soft-delete artifact records whose files are missing.")
    parser.add_argument("--yes", action="store_true", help="Confirm mutation flags.")
    args = parser.parse_args()

    init_db()
    audit = audit_artifacts()
    missing = audit["missing_storage_objects"]
    orphans = audit["orphan_storage_objects"]
    print(f"Missing artifact files: {len(missing)}")
    print(f"Orphan storage files: {len(orphans)}")

    if not (args.create_missing_records or args.soft_delete_missing_files):
        print("Dry run only. No repair flags provided.")
        return 0
    if not args.yes:
        print("Refusing to mutate artifact records without --yes.")
        return 2

    if args.soft_delete_missing_files:
        for record in missing:
            artifact_repository.soft_delete_artifact(record.artifact_id)
        print(f"Soft-deleted missing artifact records: {len(missing)}")

    if args.create_missing_records:
        # Conservative scaffold: report the action without guessing dataset/workspace metadata.
        # Use sync_filesystem_to_db.py for high-confidence historical imports.
        print("Creating missing records from arbitrary orphan files is intentionally conservative.")
        print("Run scripts/sync_filesystem_to_db.py for known dataset/report artifact imports.")

    # Touch provider to ensure configured storage is reachable.
    storage_service.get_provider().list("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
