from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func

from app.db.init_db import init_db
from app.db.models import JobRecord
from app.db.session import new_session


def main() -> int:
    init_db()
    session = new_session()
    try:
        counts = {
            status: session.query(func.count(JobRecord.id)).filter(JobRecord.status == status).scalar() or 0
            for status in ["queued", "running", "failed", "succeeded", "cancelled"]
        }
        print("Aidssist job diagnostics")
        for status, count in counts.items():
            print(f"- {status}: {count}")

        failed_jobs = (
            session.query(JobRecord)
            .filter(JobRecord.status == "failed")
            .order_by(JobRecord.finished_at.desc(), JobRecord.id.desc())
            .limit(10)
            .all()
        )
        if failed_jobs:
            print("Recent failed jobs:")
            for job in failed_jobs:
                print(f"- {job.job_id} ({job.job_type}): {job.error_message or 'No error message'}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
