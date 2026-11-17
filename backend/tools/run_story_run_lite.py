"""Run only the isolated StoryRun-lite API on IPv4 loopback."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND / "src"))

from sketch2life.infrastructure.story_run_lite.composition import (  # noqa: E402
    goal_database_url,
    verify_goal_database_owner,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic local StoryRun-lite API.")
    parser.add_argument(
        "--database-url",
        default=os.environ.get("STORYRUN_LITE_DATABASE_URL"),
        help="Owned loopback PostgreSQL URL for one storyrun_lite_* goal database.",
    )
    parser.add_argument(
        "--quarantine-root",
        default=os.environ.get("STORYRUN_LITE_QUARANTINE_ROOT"),
        help="Local private quarantine directory (defaults to the OS temporary directory).",
    )
    parser.add_argument("--port", type=int, default=8778)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or STORYRUN_LITE_DATABASE_URL is required")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    safe_url, database_name = goal_database_url(args.database_url)
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    try:
        verify_goal_database_owner(engine, database_name)
    finally:
        engine.dispose()

    os.environ["STORYRUN_LITE_DATABASE_URL"] = safe_url
    if args.quarantine_root:
        os.environ["STORYRUN_LITE_QUARANTINE_ROOT"] = str(Path(args.quarantine_root).resolve())

    try:
        import uvicorn
    except ImportError:
        parser.error("uvicorn must be installed in backend/.venv to run this API")
    uvicorn.run(
        "sketch2life.interfaces.http.story_run_lite_app:app",
        host="127.0.0.1",
        port=args.port,
        reload=False,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
