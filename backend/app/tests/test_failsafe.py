from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.preflight import run_startup_preflight
from app.repositories.user_repository import set_user_admin
from app.tests.test_auth import auth_header, enable_user_auth, login, register


CSV_FILE = {"file": ("sales.csv", b"date,sales\n2026-01-01,10\n2026-01-02,20\n", "text/csv")}


def configure_backup_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIDSSIST_BACKUP_DIR", str(tmp_path / "backups"))
    get_settings.cache_clear()


def test_preflight_endpoint_returns_ok_or_warning(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)

    response = client.get("/diagnostics/preflight")

    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "warning"}
    assert any(check["name"] == "database" for check in response.json()["checks"])


def test_preflight_detects_missing_storage_objects(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    upload = client.post("/upload", files=CSV_FILE)
    dataset_id = upload.json()["dataset_id"]
    original = tmp_path / "datasets" / dataset_id / "original.csv"
    original.unlink()

    response = client.get("/diagnostics/preflight")

    assert response.status_code == 200
    artifact_check = next(check for check in response.json()["checks"] if check["name"] == "artifacts")
    assert artifact_check["status"] == "warning"


def test_preflight_does_not_expose_secrets(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    monkeypatch.setenv("AIDSSIST_LLM_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-key")
    get_settings.cache_clear()

    response = client.get("/diagnostics/preflight")

    assert response.status_code == 200
    assert "super-secret-key" not in response.text


def test_startup_preflight_warning_does_not_raise(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    upload = client.post("/upload", files=CSV_FILE)
    dataset_id = upload.json()["dataset_id"]
    (tmp_path / "datasets" / dataset_id / "original.csv").unlink()

    run_startup_preflight()


def test_read_only_mode_blocks_upload(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_READ_ONLY_MODE", "true")
    get_settings.cache_clear()

    response = client.post("/upload", files=CSV_FILE)

    assert response.status_code == 423
    assert "read-only" in response.json()["detail"]


def test_read_only_mode_allows_health_and_dataset_list(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_READ_ONLY_MODE", "true")
    get_settings.cache_clear()

    health = client.get("/health")
    listing = client.get("/datasets")

    assert health.status_code == 200
    assert listing.status_code == 200


def test_safe_mode_blocks_risky_post(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_SAFE_MODE", "true")
    get_settings.cache_clear()

    response = client.post("/datasets/abc/analyze")

    assert response.status_code == 503
    assert "safe mode" in response.json()["detail"]


def test_create_backup_succeeds_and_contains_manifest(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    client.post("/upload", files=CSV_FILE)

    response = client.post("/backups", json={"include_storage": True, "include_reports": True})

    assert response.status_code == 201
    backup_path = tmp_path / "backups" / response.json()["filename"]
    assert backup_path.is_file()
    with ZipFile(backup_path) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert all(not name.startswith(".env") for name in names)
        assert all("aidssist_backup_" not in name for name in names if name != backup_path.name)


def test_backup_list_and_download_work(client: TestClient, monkeypatch, tmp_path: Path) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    created = client.post("/backups", json={"include_storage": False, "include_reports": False}).json()

    listing = client.get("/backups")
    download = client.get(f"/backups/{created['backup_id']}/download")

    assert listing.status_code == 200
    assert created["backup_id"] in {item["backup_id"] for item in listing.json()["backups"]}
    assert download.status_code == 200
    assert download.content.startswith(b"PK")


def test_non_admin_cannot_create_or_download_backup_when_auth_enabled(
    client: TestClient, monkeypatch, tmp_path: Path
) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    enable_user_auth(monkeypatch)
    register(client)
    token = login(client)

    create = client.post("/backups", json={"include_storage": False}, headers=auth_header(token))
    download = client.get("/backups/does-not-matter/download", headers=auth_header(token))

    assert create.status_code == 403
    assert download.status_code == 403


def test_admin_can_create_and_download_backup_when_auth_enabled(
    client: TestClient, monkeypatch, tmp_path: Path
) -> None:
    configure_backup_dir(monkeypatch, tmp_path)
    enable_user_auth(monkeypatch)
    admin = register(client, email="admin@example.com")
    set_user_admin(admin["id"], True)
    token = login(client, email="admin@example.com")

    create = client.post("/backups", json={"include_storage": False}, headers=auth_header(token))
    download = client.get(f"/backups/{create.json()['backup_id']}/download", headers=auth_header(token))

    assert create.status_code == 201
    assert download.status_code == 200


def test_restore_script_rejects_unsafe_zip_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", "{}")
        archive.writestr("../escape.txt", "bad")

    result = subprocess.run(
        [sys.executable, "scripts/restore_backup.py", str(archive_path)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Unsafe archive member path" in result.stdout


def test_create_backup_script_works(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_BACKUP_DIR", str(tmp_path / "backups"))
    monkeypatch.setenv("AIDSSIST_DATABASE_URL", f"sqlite:///{tmp_path / 'script.db'}")
    result = subprocess.run(
        [sys.executable, "scripts/create_backup.py", "--no-storage", "--no-reports"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Backup created:" in result.stdout


def test_recover_jobs_dry_run_works(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_DATABASE_URL", f"sqlite:///{tmp_path / 'recover.db'}")
    result = subprocess.run(
        [sys.executable, "scripts/recover_jobs.py"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Stale running jobs:" in result.stdout


def test_repair_artifacts_dry_run_works(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_DATABASE_URL", f"sqlite:///{tmp_path / 'repair.db'}")
    monkeypatch.setenv("AIDSSIST_STORAGE_LOCAL_ROOT", str(tmp_path / "datasets"))
    result = subprocess.run(
        [sys.executable, "scripts/repair_artifacts.py"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Dry run only" in result.stdout
