"""One-shot local operator reconciliation for the verified FEAT-085 dispatch rejection.

This performs read-only preflight, then calls the audited application repository transition. It
never writes SQL directly and must not be used for timeouts or transport-ambiguous requests.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sqlalchemy import select


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--provider-rejection",
        required=True,
        choices=("MODAL_RESOURCE_EXHAUSTED_NO_CALL_ID",),
    )
    args = parser.parse_args()
    if os.environ.get("SKETCH2LIFE_ENV") not in {"local", "test"}:
        print(json.dumps({"reconciled": False, "reason": "NON_LOCAL_ENVIRONMENT"}))
        return 2

    factory = create_core_session_factory(create_core_engine())
    with factory() as session:
        run = (
            session.execute(
                select(
                    story_tables.story_runs.c.run_id,
                    story_tables.story_runs.c.actor_scope_kind,
                    story_tables.story_runs.c.run_state,
                    story_tables.story_runs.c.job_state,
                    story_tables.story_runs.c.retryable,
                    story_tables.story_runs.c.error_code,
                    story_tables.story_runs.c.revision,
                    story_tables.story_runs.c.current_input_revision,
                ).where(story_tables.story_runs.c.run_id == args.run_id)
            )
            .mappings()
            .one_or_none()
        )
        if (
            run is None
            or run["actor_scope_kind"] != "PARENT_ACCOUNT"
            or run["run_state"] != "INPUT_PROCESSING"
            or run["job_state"] != "AWAITING_RECONCILIATION"
            or run["retryable"]
            or run["error_code"] != "DRAWING_OUTCOME_UNKNOWN"
            or not isinstance(run["revision"], int)
            or not isinstance(run["current_input_revision"], int)
        ):
            print(json.dumps({"reconciled": False, "reason": "PRECONDITION_MISMATCH"}))
            return 3
        input_row = (
            session.execute(
                select(
                    story_tables.run_inputs.c.original_asset_ref,
                    story_tables.run_inputs.c.derived_asset_ref,
                    story_tables.run_inputs.c.derived_sha256,
                ).where(
                    story_tables.run_inputs.c.run_id == args.run_id,
                    story_tables.run_inputs.c.input_revision
                    == run["current_input_revision"],
                )
            )
            .mappings()
            .one_or_none()
        )
        if (
            input_row is None
            or not input_row["original_asset_ref"]
            or not input_row["derived_asset_ref"]
            or not isinstance(input_row["derived_sha256"], str)
            or len(input_row["derived_sha256"]) != 64
        ):
            print(
                json.dumps({"reconciled": False, "reason": "ATTACHED_DRAWING_MISSING"})
            )
            return 4

        reconciled = SqlParentStoryRunRepository(
            session
        ).reconcile_modal_resource_exhausted_rejection(
            run_id=args.run_id,
            expected_run_revision=int(run["revision"]),
            expected_input_revision=int(run["current_input_revision"]),
            expected_derived_sha256=input_row["derived_sha256"],
        )
        if not reconciled:
            print(json.dumps({"reconciled": False, "reason": "CAS_REJECTED"}))
            return 5

        updated = (
            session.execute(
                select(
                    story_tables.story_runs.c.run_state,
                    story_tables.story_runs.c.job_state,
                    story_tables.story_runs.c.revision,
                    story_tables.story_runs.c.current_input_revision,
                ).where(story_tables.story_runs.c.run_id == args.run_id)
            )
            .mappings()
            .one()
        )
        print(
            json.dumps(
                {
                    "reconciled": True,
                    "run_id": args.run_id,
                    "run_state": updated["run_state"],
                    "job_state": updated["job_state"],
                    "run_revision": updated["revision"],
                    "input_revision": updated["current_input_revision"],
                    "audit_decision": args.provider_rejection,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
