from __future__ import annotations

import argparse
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import init_db
from app.services import storage_service
from app.services.artifact_service import audit_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Aidssist storage artifacts.")
    parser.add_argument("--delete-orphans", action="store_true", help="Delete local objects without DB artifact records.")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive orphan deletion.")
    args = parser.parse_args()

    init_db()
    result = audit_artifacts()
    missing = result["missing_storage_objects"]
    orphans = result["orphan_storage_objects"]

    print(f"Total active artifacts: {result['total_artifacts']}")
    print(f"Missing storage objects: {len(missing)}")
    print(f"Orphan storage objects: {len(orphans)}")
    print(f"Soft-deleted artifacts: {result['soft_deleted_artifacts']}")

    if missing:
        print("Missing artifact keys:")
        for record in missing[:20]:
            print(f"  - {record.artifact_type}: {record.storage_key}")

    if orphans:
        print("Orphan object keys:")
        for stored in orphans[:20]:
            print(f"  - {stored.key}")

    if args.delete_orphans:
        if not args.yes:
            print("Refusing to delete orphans without --yes.")
            return 2
        provider = storage_service.get_provider()
        for stored in orphans:
            provider.delete(stored.key)
        print(f"Deleted orphan storage objects: {len(orphans)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
