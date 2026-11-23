"""One-time, re-runnable reconciliation of pre-existing DELETE_PENDING runs (DTR §6.4).

For every Parent or Teacher (organization) run in ``DELETE_PENDING`` that has no outbox event for
its aggregate, the tool inserts ``StoryRunCancellationRequestedV1`` with the deterministic event
id and the aggregate row of the run's own owner scope (insert-if-absent; T-13a widened the target
set from Parent runs to Teacher runs). Runs cancelled by the FR-C-08 code already have their event
and are skipped; a second run inserts nothing. It is used only on a deployment where the Parent
router is mounted (S19).

Owner-run only. The database target must pass the same fail-closed allow-list as the lifecycle
consumer (loopback, port not 5432/5433, name containing ``frc08``, equal to
``FRC08_ALLOWED_DATABASE``/``FRC08_ALLOWED_PORT``); no object store is contacted.

    python tools/frc08_reconcile_delete_pending.py
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

from tools.run_be1_lifecycle_consumer import TargetRefused, build_engine, load_targets


def reconcile(store: object, *, page_size: int = 500) -> tuple[int, int]:
    """Return (eligible runs seen, events inserted)."""

    from sketch2life.infrastructure.persistence.story_lifecycle_store import (
        SqlStoryLifecycleStore,
    )

    if not isinstance(store, SqlStoryLifecycleStore):
        raise TypeError("reconciliation needs the Story lifecycle store")
    seen = 0
    inserted = 0
    for run_id in store.delete_pending_runs_without_event(limit=page_size):
        seen += 1
        if store.insert_reconciliation_event(run_id):
            inserted += 1
    return seen, inserted


def main(environ: Mapping[str, str] | None = None) -> int:
    from sqlalchemy.orm import sessionmaker

    from sketch2life.infrastructure.persistence.story_lifecycle_store import (
        SqlStoryLifecycleStore,
    )

    env = os.environ if environ is None else environ
    try:
        targets = load_targets(env, require_storage=False)
    except TargetRefused as refused:
        print(f"REFUSED code={refused.code}", file=sys.stderr)
        return 2
    engine = build_engine(targets)
    try:
        store = SqlStoryLifecycleStore(sessionmaker(engine, expire_on_commit=False))
        seen, inserted = reconcile(store)
    finally:
        engine.dispose()
    print(f"FRC08_RECONCILE_DONE eligible={seen} inserted={inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
