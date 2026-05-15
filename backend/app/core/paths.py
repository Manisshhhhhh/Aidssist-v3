import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DATASETS_DIR = Path(
    os.getenv("AIDSSIST_STORAGE_LOCAL_ROOT")
    or os.getenv("AIDSSIST_DATASETS_DIR", PROJECT_ROOT / "datasets")
).expanduser()
REPORTS_DIR = Path(
    os.getenv("AIDSSIST_REPORTS_LOCAL_ROOT")
    or os.getenv("AIDSSIST_REPORTS_DIR", PROJECT_ROOT / "reports")
).expanduser()
