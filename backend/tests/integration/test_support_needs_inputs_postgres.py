"""T-12c PostgreSQL acceptance: support needs never reach a run snapshot or a worker input.

SRS l.932 (support needs stay out of AI context and run snapshots), l.1922. A profile with a
stored support-needs record (a unique sentinel in the category and the note) runs the real first
story path through the confirmation route; the worker input the generator receives, every persisted
run row and every answer of the Parent routes are searched, key by key and value by value, for the
sentinel. The static guard (no builder module mentions the feature) is in
``tests/unit/test_support_needs.py``. This module reuses the T-12a fixtures, so it runs on a
disposable database whose name contains ``frc08_v4_t12a`` and ``be1_acceptance``.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, text

from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.interfaces.http.support_needs_runtime import SupportNeedsRuntime
from tests.integration.test_parent_activity_selection_postgres import (  # noqa: F401
    ActivityApi,
    story_rows,
)
from tests.integration.test_parent_profile_context_postgres import (  # noqa: F401
    add_entry,
    api,
    confirm,
    entry_id_of,
    headers,
    input_rows,
    make_profile,
    ready_run,
)
from tests.integration.test_support_needs_postgres import CATEGORY, SENTINEL, make_crypto


def _strings(value: Any) -> list[str]:
    """Every key and every string value of a nested structure."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found.extend(_strings(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_strings(item))
    elif value is not None:
        found.append(str(value))
    return found


def test_a_stored_support_record_never_reaches_a_snapshot_a_worker_input_or_a_view(
    api: ActivityApi,  # noqa: F811
) -> None:
    api.app.state.support_needs_runtime = SupportNeedsRuntime(crypto=make_crypto())
    profile = make_profile(api, api.parent)
    stored = api.client.put(
        f"/v1/parent/profiles/{profile}/support-needs",
        json={"expected_revision": 0, "category": CATEGORY, "note": SENTINEL},
        headers=headers(api.parent, "support-1"),
    )
    assert stored.status_code == 200, stored.text
    entry = entry_id_of(add_entry(api, api.parent, profile, "thich cho ca an"))
    run_id = ready_run(api, api.parent, profile)
    response = confirm(api, api.parent, run_id, [entry])
    assert response.status_code == 200, response.text
    assert SENTINEL not in response.text and CATEGORY not in response.text

    # the worker input of the first story: no key and no value mentions a support need
    (worker,) = api.generator.inputs[:1]
    for item in _strings(worker):
        assert SENTINEL not in item and CATEGORY not in item
        assert "support" not in item.lower()
    assert "support_needs" not in json.dumps(worker, default=str)

    # every persisted run row: the context snapshots, the story rows and the run itself
    snapshots = [row["context_snapshot"] for row in input_rows(api, run_id)]
    assert len(snapshots) == 3  # the two seeded revisions and the selected-context one
    for snapshot in snapshots:
        for item in _strings(snapshot):
            assert SENTINEL not in item and "support" not in item.lower()
    with api.sessions()() as db:
        for table in (story_tables.run_inputs, story_tables.story_runs):
            dumped = json.dumps(
                [dict(row) for row in db.execute(select(table)).mappings().all()], default=str
            )
            assert SENTINEL not in dumped and CATEGORY not in dumped
        story = json.dumps([dict(row) for row in story_rows(api, run_id)], default=str)
        assert SENTINEL not in story and CATEGORY not in story
        # the only places the sentinel is stored are two ciphertext columns, and only encrypted
        holders = db.scalar(
            text(
                "SELECT count(*) FROM parent.profile_support_needs "
                "WHERE position(convert_to(:s, 'UTF8') in ciphertext) > 0"
            ),
            {"s": SENTINEL},
        )
        assert holders == 0

    # the ordinary projections of the profile and its run
    for path in (
        f"/v1/parent/profiles/{profile}",
        "/v1/parent/profiles",
        f"/v1/parent/profiles/{profile}/context-entries",
        f"/v1/story-runs/{run_id}",
    ):
        read = api.client.get(path, headers=headers(api.parent))
        assert read.status_code == 200, (path, read.text)
        assert SENTINEL not in read.text and CATEGORY not in read.text
        assert "support" not in read.text.lower()
    # and the record is still readable through its own route
    own = api.client.get(
        f"/v1/parent/profiles/{profile}/support-needs", headers=headers(api.parent)
    )
    assert own.json()["note"] == SENTINEL and own.json()["revision"] == 1
