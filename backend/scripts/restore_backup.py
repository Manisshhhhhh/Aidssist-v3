from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import socket
import sys
from zipfile import ZipFile


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.core import paths
from app.services.backup_service import create_backup, sqlite_db_path


class RestoreError(Exception):
    """Raised when a backup cannot be restored safely."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore an Aidssist backup zip. This is CLI-only by design.")
    parser.add_argument("backup", help="Path to backup zip.")
    parser.add_argument("--yes", action="store_true", help="Actually restore. Without this flag, performs validation only.")
    parser.add_argument("--force", action="store_true", help="Allow restore even if the local backend port appears open.")
    args = parser.parse_args()

    backup_path = Path(args.backup).expanduser().resolve()
    try:
        validate_backup(backup_path)
        if backend_port_open() and not args.force:
            raise RestoreError("Backend appears to be running on 127.0.0.1:8000. Stop it or pass --force.")
        if not args.yes:
            print("Backup validation passed. Re-run with --yes to restore.")
            return 0
        pre_backup = create_backup()
        print(f"Pre-restore backup created: {pre_backup.filename}")
        restore_backup(backup_path)
        print("Restore completed. Run preflight and smoke tests before resuming normal use.")
        return 0
    except RestoreError as exc:
        print(f"FAIL: {exc}")
        return 1


def validate_backup(backup_path: Path) -> None:
    if not backup_path.is_file():
        raise RestoreError(f"Backup does not exist: {backup_path}")
    with ZipFile(backup_path) as archive:
        names = archive.namelist()
        if "manifest.json" not in names:
            raise RestoreError("Backup is missing manifest.json.")
        for name in names:
            if is_unsafe_archive_name(name):
                raise RestoreError(f"Unsafe archive member path: {name}")
        try:
            json.loads(archive.read("manifest.json").decode("utf-8"))
        except Exception as exc:
            raise RestoreError("Backup manifest is not valid JSON.") from exc


def restore_backup(backup_path: Path) -> None:
    settings = get_settings()
    db_path = sqlite_db_path()
    datasets_root = paths.DATASETS_DIR.expanduser()
    reports_root = Path(settings.reports_local_root).expanduser()

    with ZipFile(backup_path) as archive:
        if db_path and "database/aidssist.db" in archive.namelist():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with archive.open("database/aidssist.db") as source, db_path.open("wb") as target:
                shutil.copyfileobj(source, target)
        extract_prefix(archive, "datasets/", datasets_root)
        extract_prefix(archive, "reports/", reports_root)


def extract_prefix(archive: ZipFile, prefix: str, destination_root: Path) -> None:
    members = [name for name in archive.namelist() if name.startswith(prefix) and not name.endswith("/")]
    if not members:
        return
    if destination_root.exists():
        shutil.rmtree(destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    for name in members:
        relative = Path(name.removeprefix(prefix))
        destination = (destination_root / relative).resolve()
        if not is_relative_to(destination, destination_root.resolve()):
            raise RestoreError(f"Unsafe restore target: {name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target)


def is_unsafe_archive_name(name: str) -> bool:
    path = Path(name)
    return path.is_absolute() or ".." in path.parts or "\\" in name


def backend_port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", 8000)) == 0


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
