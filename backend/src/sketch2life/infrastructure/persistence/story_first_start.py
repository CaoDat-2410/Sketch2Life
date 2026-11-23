"""The implicit first-story start of a Parent StoryRun (goal v4 T-2e-a, D1-D4, SRS l.394, l.1412).

There is no "generate the first story" command in the SRS (l.1664-1671): the first story starts by
itself once the adult has confirmed the subject, chosen the main activity and confirmed the context
(l.1412). ``FirstStoryStarter.start_if_ready`` is called by the command that may complete the last
gate (``activity-selection``, ``context-confirmation``), inside that command's transaction and under
its run row lock, after its own writes and before its commit. It never commits: a failure rolls the
whole command back.

V4-A OPEN-A D1-D3: a Teacher run starts through the same class (predicate P_T on the pin made at
create instead of a selection row; the worker input carries the Teacher direction, no activity),
triggered by ``context-confirmation`` and ``subject-confirmation``.

The start is modelled on ``reserve_story_rewrite``: story revision 1 ``GENERATING``, run
``SCRIPT_GENERATING`` with ``job_state QUEUED``, no receipt of its own (the command's receipt is the
only one), so the existing runner, the reaper and the completion path apply unchanged. The worker
input is ``sketch2life.story-generation-input.v2``: the rewrite input without the rewrite fields and
with the selected main activity.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.domain.story_teacher import teacher_lesson_direction, teacher_pin_ready
from sketch2life.infrastructure.story_run_lite import tables as story_tables

FIRST_STORY_INPUT_SCHEMA = "sketch2life.story-generation-input.v2"
# The first story reuses the rewrite identifiers until the generator reports its own (DEV-2); a unit
# test pins them equal to ``story_inputs.story_generation`` (importing it here would be circular).
FIRST_STORY_MODEL_ID = "story-generator-port"
FIRST_STORY_MODEL_REVISION = "unassigned"
FIRST_STORY_PROMPT_VERSION = "parent-story-rewrite.v1"
# The activity fields the worker receives (title, objective, instructions, safety notes, kind,
# source, lesson id, version id, content hash).
_WORKER_ACTIVITY_FIELDS = (
    "title",
    "objective",
    "instructions_text",
    "safety_notes",
    "activity_kind",
)

# The probe of ``_story_generation_basis`` reduced to "not ready" (``None``) or its four results.
Basis = tuple[RowMapping, RowMapping, str, list[str]]
Probe = Callable[[VerifiedPrincipal, Mapping[Any, Any], int], Basis | None]


def latest_selection_row(
    session: Session, run_id: str, understanding_revision: int
) -> RowMapping | None:
    """The newest selection of the run for this understanding revision (the one the story uses)."""

    table = story_tables.activity_selections
    return (
        session.execute(
            select(table)
            .where(
                table.c.run_id == run_id,
                table.c.target_understanding_revision == understanding_revision,
            )
            .order_by(table.c.selection_no.desc())
            .limit(1)
        )
        .mappings()
        .one_or_none()
    )


def worker_activity(selection: Mapping[Any, Any]) -> dict[str, Any]:
    """The bounded activity object of the v2 worker input, taken from the stored snapshot."""

    snapshot = selection["activity_snapshot"]
    activity = {name: snapshot[name] for name in _WORKER_ACTIVITY_FIELDS}
    return {
        **activity,
        "source": snapshot["source"],
        "lesson_id": selection["lesson_id"],
        "version_id": selection["version_id"],
        "content_sha256": selection["content_sha256"],
    }


class FirstStoryStarter:
    """Reserve story revision 1 inside the caller's transaction when every gate is met.

    A Parent run needs its chosen main activity (predicate P, T-2e-a). A Teacher run (V4-A OPEN-A
    D1-D3) has no selection: it needs the complete pin made at create (predicate P_T) and the
    worker input carries the Teacher direction instead of an activity. ``enabled`` is off for the
    job-side repository only.
    """

    def __init__(
        self,
        session: Session,
        *,
        enabled: bool,
        probe: Probe,
        live_run: Callable[[str], Any],
        sha256_json: Callable[[Any], str],
        teacher: bool = False,
    ) -> None:
        self._session = session
        self._enabled = enabled
        self._probe = probe
        self._live_run = live_run
        self._sha256_json = sha256_json
        self._teacher = teacher

    def start_if_ready(
        self,
        run_id: str,
        principal: VerifiedPrincipal,
        now: datetime,
        *,
        generator_supports_role: bool = True,
    ) -> ParentStoryRevisionReservation | None:
        """The reservation of revision 1, or ``None`` when a gate is unmet (nothing is written).

        ``generator_supports_role`` is computed by the route (a composed generator that refuses
        the actor's role must not receive the story, V4-A OPEN-A D4)."""

        if not self._enabled or not generator_supports_role:
            return None
        try:
            return self._start(run_id, principal, now)
        except SQLAlchemyError:
            # Reads and writes alike: roll the whole command back and say so plainly (the callers'
            # IntegrityError handlers would otherwise report an idempotency or confirmation
            # conflict).
            self._session.rollback()
            raise ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE") from None

    def _start(
        self, run_id: str, principal: VerifiedPrincipal, now: datetime
    ) -> ParentStoryRevisionReservation | None:
        runs = story_tables.story_runs
        run = self._session.execute(select(runs).where(runs.c.run_id == run_id)).mappings().one()
        if run["run_state"] != "PREPARATION_REVIEW":
            return None
        revisions = story_tables.story_revisions
        if (
            self._session.scalar(
                select(revisions.c.story_revision_id).where(revisions.c.run_id == run_id).limit(1)
            )
            is not None
        ):
            return None
        if self._teacher and run["occurrence_ref"] is None:
            return None  # a T-4a1/T-13a fixture run has no occurrence pin: it never starts a story
        understanding_revision = int(run["understanding_revision"] or 0)
        selection: RowMapping | None = None
        if not self._teacher:
            selection = latest_selection_row(self._session, run_id, understanding_revision)
            if selection is None:
                return None
        basis = self._probe(principal, run, understanding_revision)
        if basis is None:
            return None
        _, input_row, idea_text, visible_features = basis
        if self._teacher and not teacher_pin_ready(
            input_row["lesson_pin_snapshot"], run["occurrence_ref"]
        ):
            return None
        context = input_row["context_snapshot"]
        worker_input = {
            "schema_version": FIRST_STORY_INPUT_SCHEMA,
            "role": "TEACHER" if self._teacher else "PARENT",
            "language": "vi",
            "confirmed_subject": str(run["subject_label"] or "").strip(),
            "understanding_revision": understanding_revision,
            "drawing_sha256": str(input_row["original_sha256"]),
            "visible_features": visible_features,
            "child_age_months": int(context["age_months"]),
            "context_revision": int(input_row["context_revision"]),
            "adult_confirmed_idea": idea_text,
            "activity": worker_activity(selection) if selection is not None else None,
            "lesson_direction": teacher_lesson_direction(context) if self._teacher else None,
        }
        request_hash = self._sha256_json(worker_input)
        story_revision_id = str(uuid4())
        new_version = int(run["version"]) + 1
        new_revision = int(run["revision"]) + 1
        self._session.execute(
            insert(revisions).values(
                story_revision_id=story_revision_id,
                run_id=run_id,
                revision_no=1,
                status="GENERATING",
                source_asset_sha256=str(input_row["original_sha256"]),
                understanding_revision=understanding_revision,
                context_revision=int(input_row["context_revision"]),
                schema_version="sketch2life.story-revision.v1",
                prompt_version=FIRST_STORY_PROMPT_VERSION,
                model_id=FIRST_STORY_MODEL_ID,
                model_revision=FIRST_STORY_MODEL_REVISION,
                request_sha256=request_hash,
                created_at=now,
            )
        )
        self._session.execute(
            update(runs)
            .where(self._live_run(run_id))
            .values(
                run_state="SCRIPT_GENERATING",
                job_state="QUEUED",
                retryable=False,
                error_code=None,
                version=new_version,
                revision=new_revision,
                updated_at=now,
            )
        )
        return ParentStoryRevisionReservation(
            run_id=run_id,
            story_revision_id=story_revision_id,
            revision_no=1,
            understanding_revision=understanding_revision,
            context_revision=int(input_row["context_revision"]),
            source_asset_sha256=str(input_row["original_sha256"]),
            worker_input=worker_input,
            request_sha256=request_hash,
            receipt_id=None,
            organization_id=str(run["actor_scope_ref"]) if self._teacher else None,
        )


__all__ = [
    "FIRST_STORY_INPUT_SCHEMA",
    "FIRST_STORY_MODEL_ID",
    "FIRST_STORY_MODEL_REVISION",
    "FIRST_STORY_PROMPT_VERSION",
    "FirstStoryStarter",
    "latest_selection_row",
    "worker_activity",
]
