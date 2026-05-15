from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.models import JobRecord
from app.db.session import new_session


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover stale Aidssist jobs.")
    parser.add_argument("--apply", action="store_true", help="Mutate stale jobs. Default is dry run.")
    args = parser.parse_args()

    init_db()
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.job_stale_after_minutes)
    session = new_session()
    try:
        stale_jobs = (
            session.query(JobRecord)
            .filter(JobRecord.status == "running", JobRecord.started_at < cutoff)
            .order_by(JobRecord.started_at.asc())
            .all()
        )
        print(f"Stale running jobs: {len(stale_jobs)}")
        for job in stale_jobs:
            action = "requeue" if job.attempts < job.max_attempts else "fail"
            print(f"- {job.job_id} ({job.job_type}) attempts={job.attempts}/{job.max_attempts}: {action}")
            if args.apply:
                if action == "requeue":
                    job.status = "queued"
                    job.progress = 0
                    job.started_at = None
                    job.error_message = "Recovered from stale running state."
                else:
                    job.status = "failed"
                    job.finished_at = datetime.now(timezone.utc)
                    job.error_message = "Marked failed by recover_jobs because the job was stale."
        if args.apply:
            session.commit()
            print("Applied stale job recovery.")
        else:
            print("Dry run only. Re-run with --apply to mutate jobs.")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
