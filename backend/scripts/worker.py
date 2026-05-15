from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings
from app.db.init_db import init_db
from app.services.job_runner import run_next_job_once


should_stop = False


def request_stop(signum, frame) -> None:  # noqa: ANN001
    global should_stop
    should_stop = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Aidssist background job worker.")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job and exit.")
    parser.add_argument("--poll-interval", type=float, default=None, help="Seconds to sleep when no jobs are queued.")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    init_db()

    poll_interval = args.poll_interval or get_settings().job_poll_interval_seconds
    print("Aidssist worker started.")

    while not should_stop:
        record = run_next_job_once()
        if record is None:
            if args.once:
                print("No queued jobs.")
                return 0
            time.sleep(poll_interval)
            continue

        print(f"Processed job {record.job_id} ({record.job_type}) -> {record.status}")
        if args.once:
            return 0 if record.status == "succeeded" else 1

    print("Aidssist worker stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
