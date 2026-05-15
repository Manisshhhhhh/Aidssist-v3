from __future__ import annotations

import argparse
from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.init_db import init_db
from app.models.backup_models import BackupRequest
from app.services.backup_service import backup_root, create_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an Aidssist backup zip.")
    parser.add_argument("--no-storage", action="store_true", help="Exclude dataset storage.")
    parser.add_argument("--no-reports", action="store_true", help="Exclude reports storage.")
    args = parser.parse_args()

    init_db()
    backup = create_backup(
        BackupRequest(
            include_storage=not args.no_storage,
            include_reports=not args.no_reports,
        )
    )
    print(f"Backup created: {backup_root() / backup.filename}")
    print(f"Backup id: {backup.backup_id}")
    print(f"Size bytes: {backup.size_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
