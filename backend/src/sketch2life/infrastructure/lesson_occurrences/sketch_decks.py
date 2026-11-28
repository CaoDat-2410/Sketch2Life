"""Persistence service for Teacher Sketch Deck revisions and idempotent generation commands."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, NoReturn, cast
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.svg_catalog import SvgCatalogPort
from sketch2life.domain.lesson_occurrences.plan import canonical_hash
from sketch2life.domain.lesson_occurrences.sketch_deck import (
    DrawingStepInput,
    SketchDeckDrawingInputs,
    SketchDeckRuleError,
    SketchDeckStep,
    drawing_inputs_payload,
    revision_content_hash,
    validate_drawing_inputs,
    validate_ready_steps,
)
from sketch2life.infrastructure.lesson_library.tables import LIBRARY_VERSIONS
from sketch2life.infrastructure.lesson_occurrences.documents import DocumentError
from sketch2life.infrastructure.lesson_occurrences.scope import (
    authorize_occurrence,
    not_found,
)
from sketch2life.infrastructure.lesson_occurrences.sketch_deck_drawing import (
    attach_progressive_drawing,
    drawing_from_ai_draft,
    resolve_local_drawing,
)
from sketch2life.infrastructure.lesson_occurrences.sketch_deck_tables import (
    SKETCH_DECK_REVISIONS,
    SKETCH_DECK_STEPS,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    OCCURRENCES,
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel

CREATE_RECEIPT_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/sketch-decks"
DECK_SCHEMA_VERSION = "sketch2life.teacher-sketch-deck.v1"
WORKER_INPUT_SCHEMA_VERSION = "sketch2life.teacher-deck-input.v1"
PROMPT_TEMPLATE_VERSION = "NOT_VERIFIED"
MODEL_CONFIG_VERSION = "modal-model-profile-v1"
_AGE_BAND_WORKER_MONTHS = {
    # The worker accepts one numeric target. These values are generic band midpoints; no profile
    # or roster age is read or sent. The pinned target_age_band remains the canonical stored value.
    "age-36-71-months-v1": 54,
    # Older lesson versions may carry this unversioned band ref; preserve it on the deck revision.
    "36-71": 54,
    "age-72-107-months-v1": 90,
    "age-108-120-months-v1": 114,
}


def _age_band_worker_months(value: object) -> int | None:
    return _AGE_BAND_WORKER_MONTHS.get(value) if isinstance(value, str) else None


def _raise_invalid_worker_plan_field(db: Session, field: str) -> NoReturn:
    db.rollback()
    raise DocumentError(
        400,
        "INVALID_REQUEST",
        field_errors=[{"field": field, "code": "INVALID_FORMAT"}],
    )


@dataclass(frozen=True, slots=True)
class SketchDeckCommandResult:
    body: dict[str, Any]
    status_code: int
    replayed: bool


@dataclass(frozen=True, slots=True)
class PreparedSketchDeck:
    occurrence_id: str
    plan_revision_id: str
    plan_content_hash: str
    plan_activity_ids: tuple[str, ...]
    target_age_band: str
    drawing_inputs: SketchDeckDrawingInputs
    worker_input: dict[str, Any]
    drawing: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SketchDeckGenerationStart:
    sketch_deck_revision_id: str
    revision_no: int
    occurrence_id: str
    plan_revision_id: str
    plan_content_hash: str
    target_age_band: str
    plan_activity_ids: tuple[str, ...]
    drawing: dict[str, Any] | None = None


class SketchDeckRevisionService:
    """SQL adapter and command service; no provider call is made while a DB lock is held."""

    def __init__(self, db: Session, *, svg_catalog: SvgCatalogPort | None = None) -> None:
        self.db = db
        self.svg_catalog = svg_catalog

    @staticmethod
    def fingerprint(
        *,
        occurrence_id: str,
        expected_plan_revision_id: str,
        expected_plan_hash: str,
        drawing_inputs: SketchDeckDrawingInputs,
    ) -> str:
        return canonical_hash(
            {
                "method": "POST",
                "route": CREATE_RECEIPT_SCOPE,
                "occurrence_id": occurrence_id,
                "expected_plan_revision_id": expected_plan_revision_id,
                "expected_plan_hash": expected_plan_hash,
                "review_inputs": drawing_inputs_payload(drawing_inputs),
            }
        )

    def replay_if_present(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        expected_plan_revision_id: str,
        expected_plan_hash: str,
        drawing_inputs: SketchDeckDrawingInputs,
        idempotency_key: str,
    ) -> SketchDeckCommandResult | None:
        authorize_occurrence(self.db, principal, occurrence_id, write=True)
        receipt = self._receipt(principal, occurrence_id, idempotency_key)
        if receipt is None:
            self.db.rollback()
            return None
        fingerprint = self.fingerprint(
            occurrence_id=occurrence_id,
            expected_plan_revision_id=expected_plan_revision_id,
            expected_plan_hash=expected_plan_hash,
            drawing_inputs=drawing_inputs,
        )
        result = self._replay(receipt, fingerprint)
        self.db.rollback()
        return result

    def verify_approved_plan(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        expected_plan_revision_id: str,
        expected_plan_hash: str,
    ) -> None:
        access = authorize_occurrence(self.db, principal, occurrence_id, write=True)
        self._approved_plan(
            occurrence=access.occurrence,
            occurrence_id=occurrence_id,
            expected_plan_revision_id=expected_plan_revision_id,
            expected_plan_hash=expected_plan_hash,
        )
        self.db.rollback()

    def prepare_worker_input(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        expected_plan_revision_id: str,
        expected_plan_hash: str,
        drawing_inputs: SketchDeckDrawingInputs,
    ) -> PreparedSketchDeck:
        """Build the worker request from reviewed inputs and the pinned approved plan."""

        try:
            drawing_inputs = validate_drawing_inputs(drawing_inputs)
        except SketchDeckRuleError as error:
            raise DocumentError(
                400,
                error.code,
                field_errors=[
                    {"field": error.field or "review_inputs", "code": "INVALID_FORMAT"}
                ],
            ) from None

        access = authorize_occurrence(self.db, principal, occurrence_id, write=True)
        plan = self._approved_plan(
            occurrence=access.occurrence,
            occurrence_id=occurrence_id,
            expected_plan_revision_id=expected_plan_revision_id,
            expected_plan_hash=expected_plan_hash,
        )
        source_age_band: object = None
        if plan["source_lesson_version_id"] is not None:
            source = self.db.execute(
                select(
                    LIBRARY_VERSIONS.c.content_json,
                    LIBRARY_VERSIONS.c.structured_content_hash,
                ).where(LIBRARY_VERSIONS.c.version_id == plan["source_lesson_version_id"])
            ).mappings().one_or_none()
            if (
                source is None
                or source["structured_content_hash"] != plan["source_lesson_version_hash"]
            ):
                self.db.rollback()
                raise DocumentError(409, "STALE_REVISION")
            source_content = source["content_json"]
            if not isinstance(source_content, dict):
                self.db.rollback()
                raise DocumentError(409, "SKETCH_DECK_PLAN_INCOMPLETE")
            source_age_band = source_content.get("target_age_band_ref")

        source_age_months = _age_band_worker_months(source_age_band)
        confirmed_age_band = drawing_inputs.teacher_confirmed_age_band_ref
        confirmed_age_months = _age_band_worker_months(confirmed_age_band)
        if source_age_months is not None:
            if confirmed_age_band is not None and confirmed_age_months != source_age_months:
                self.db.rollback()
                raise DocumentError(
                    400,
                    "INVALID_REQUEST",
                    field_errors=[
                        {"field": "teacher_confirmed_age_band_ref", "code": "MISMATCH"}
                    ],
                )
            target_age_band = str(source_age_band)
            target_age_months = source_age_months
        elif confirmed_age_months is not None and confirmed_age_band is not None:
            target_age_band = confirmed_age_band
            target_age_months = confirmed_age_months
        else:
            self.db.rollback()
            raise DocumentError(
                400,
                "INVALID_REQUEST",
                field_errors=[
                    {
                        "field": "teacher_confirmed_age_band_ref",
                        "code": "REQUIRED" if confirmed_age_band is None else "INVALID",
                    }
                ],
            )
        if not target_age_band:
            _raise_invalid_worker_plan_field(self.db, "teacher_confirmed_age_band_ref")
        objectives = plan.get("objectives")
        if not isinstance(objectives, list) or not 1 <= len(objectives) <= 4:
            _raise_invalid_worker_plan_field(self.db, "objectives")
        for index, objective in enumerate(objectives):
            if (
                not isinstance(objective, str)
                or not objective.strip()
                or len(objective) > 200
            ):
                _raise_invalid_worker_plan_field(self.db, f"objectives[{index}]")

        activity_rows = self.db.execute(
            select(PLAN_ACTIVITIES)
            .where(PLAN_ACTIVITIES.c.plan_revision_id == expected_plan_revision_id)
            .order_by(PLAN_ACTIVITIES.c.activity_order)
        ).mappings().all()
        if not 1 <= len(activity_rows) <= 6:
            _raise_invalid_worker_plan_field(self.db, "activities")
        activities: list[dict[str, Any]] = []
        for activity_index, row in enumerate(activity_rows):
            activity_ref = str(row["plan_activity_id"])
            if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", activity_ref) is None:
                _raise_invalid_worker_plan_field(
                    self.db, f"activities[{activity_index}].activity_ref"
                )
            if row["activity_kind"] == "LESSON":
                snapshot = row["activity_snapshot"]
                if not isinstance(snapshot, dict):
                    self.db.rollback()
                    raise DocumentError(409, "SKETCH_DECK_PLAN_INCOMPLETE")
                title = snapshot.get("title")
                raw_fields: dict[str, object] = {
                    "goal": snapshot.get("objective"),
                    "materials": snapshot.get("materials_text"),
                    "preparation": snapshot.get("preparation_text"),
                    "instructions": snapshot.get("instructions_text"),
                    "safety_notes": snapshot.get("safety_notes"),
                }
                fields: dict[str, str] = {}
                if not isinstance(title, str) or not title.strip() or len(title) > 120:
                    _raise_invalid_worker_plan_field(
                        self.db, f"activities[{activity_index}].title"
                    )
                field_limits = {
                    "goal": 200,
                    "materials": 500,
                    "preparation": 500,
                    "instructions": 1_200,
                    "safety_notes": 500,
                }
                for key, value in raw_fields.items():
                    if (
                        not isinstance(value, str)
                        or not value.strip()
                        or len(value) > field_limits[key]
                    ):
                        _raise_invalid_worker_plan_field(
                            self.db, f"activities[{activity_index}].{key}"
                        )
                    fields[key] = value
                activities.append(
                    {
                        "activity_ref": activity_ref,
                        "title": title,
                        **{key: _bounded_text_segments(value) for key, value in fields.items()},
                    }
                )
            elif row["activity_kind"] == "CUSTOM":
                title = row["custom_title"]
                description = row["custom_description"]
                checklist_result = row["checklist_result"]
                checklist_items = (
                    checklist_result.get("items")
                    if isinstance(checklist_result, dict)
                    else None
                )
                checklist_satisfied = (
                    isinstance(row["safety_checklist_version"], str)
                    and bool(row["safety_checklist_version"].strip())
                    and isinstance(checklist_items, list)
                    and bool(checklist_items)
                    and all(
                        isinstance(item, dict)
                        and set(item) == {"item_id", "checked"}
                        and isinstance(item.get("item_id"), str)
                        and bool(item["item_id"].strip())
                        and item.get("checked") is True
                        for item in checklist_items
                    )
                )
                if not isinstance(title, str) or not title.strip() or len(title) > 160:
                    _raise_invalid_worker_plan_field(
                        self.db, f"activities[{activity_index}].title"
                    )
                if (
                    not isinstance(description, str)
                    or not description.strip()
                    or len(description) > 4000
                ):
                    _raise_invalid_worker_plan_field(
                        self.db, f"activities[{activity_index}].description"
                    )
                if (
                    not isinstance(row["confirmed_by"], str)
                    or not row["confirmed_by"].strip()
                    or row["confirmed_at"] is None
                    or not checklist_satisfied
                ):
                    self.db.rollback()
                    raise DocumentError(409, "SKETCH_DECK_PLAN_INCOMPLETE")
                activities.append(
                    {
                        "activity_ref": activity_ref,
                        "title": title,
                        "description": description,
                    }
                )
            else:
                _raise_invalid_worker_plan_field(
                    self.db, f"activities[{activity_index}].activity_kind"
                )

        plan_without_hash: dict[str, Any] = {
            "schema_version": WORKER_INPUT_SCHEMA_VERSION,
            "plan_revision_ref": expected_plan_revision_id,
            "topic": drawing_inputs.topic,
            "target_age_months": target_age_months,
            "objectives": list(objectives),
            "drawing_steps": [
                {
                    "step_index": index,
                    "action": step.action,
                    "placement": step.placement,
                }
                for index, step in enumerate(drawing_inputs.drawing_steps, start=1)
            ],
            "drawing_subject": drawing_inputs.topic,
            "subject_knowledge": list(drawing_inputs.subject_knowledge),
            "activities": activities,
        }
        drawing = resolve_local_drawing(
            subject=drawing_inputs.topic,
            target_age_band=target_age_band,
            catalog=self.svg_catalog,
        )
        if drawing is not None:
            plan_without_hash["drawing_source_available"] = True
        worker_input = {
            **plan_without_hash,
            "content_hash": hashlib.sha256(
                json.dumps(
                    plan_without_hash,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }
        result = PreparedSketchDeck(
            occurrence_id=occurrence_id,
            plan_revision_id=expected_plan_revision_id,
            plan_content_hash=expected_plan_hash,
            plan_activity_ids=tuple(str(row["plan_activity_id"]) for row in activity_rows),
            target_age_band=target_age_band,
            drawing_inputs=drawing_inputs,
            worker_input=worker_input,
            drawing=drawing,
        )
        self.db.rollback()
        return result

    def begin_generation(
        self,
        *,
        principal: VerifiedPrincipal,
        prepared: PreparedSketchDeck,
        idempotency_key: str,
        model_profile_ref: str,
        model_profile_version: str,
    ) -> SketchDeckGenerationStart | SketchDeckCommandResult:
        fingerprint = self.fingerprint(
            occurrence_id=prepared.occurrence_id,
            expected_plan_revision_id=prepared.plan_revision_id,
            expected_plan_hash=prepared.plan_content_hash,
            drawing_inputs=prepared.drawing_inputs,
        )
        scope = CREATE_RECEIPT_SCOPE.format(occurrence_id=prepared.occurrence_id)
        try:
            access = authorize_occurrence(
                self.db, principal, prepared.occurrence_id, write=True, lock="update"
            )
            self._approved_plan(
                occurrence=access.occurrence,
                occurrence_id=prepared.occurrence_id,
                expected_plan_revision_id=prepared.plan_revision_id,
                expected_plan_hash=prepared.plan_content_hash,
            )
            receipt = self._receipt(principal, prepared.occurrence_id, idempotency_key)
            if receipt is not None:
                result = self._replay(receipt, fingerprint)
                self.db.rollback()
                return result

            revision_no = int(
                self.db.scalar(
                    select(func.coalesce(func.max(SKETCH_DECK_REVISIONS.c.revision_no), 0)).where(
                        SKETCH_DECK_REVISIONS.c.occurrence_id == prepared.occurrence_id
                    )
                )
                or 0
            ) + 1
            revision_id = str(uuid4())
            now = datetime.now(UTC)
            config_hash = canonical_hash(
                {
                    "workload": "teacher.sketch-deck.generate",
                    "input_schema_version": WORKER_INPUT_SCHEMA_VERSION,
                    "model_profile_ref": model_profile_ref,
                    "model_profile_version": model_profile_version,
                    "prompt_template_version": PROMPT_TEMPLATE_VERSION,
                    "config_version": MODEL_CONFIG_VERSION,
                    "review_inputs": drawing_inputs_payload(prepared.drawing_inputs),
                }
            )
            self.db.execute(
                SKETCH_DECK_REVISIONS.insert().values(
                    sketch_deck_revision_id=revision_id,
                    occurrence_id=prepared.occurrence_id,
                    plan_revision_id=prepared.plan_revision_id,
                    revision_no=revision_no,
                    plan_content_hash=prepared.plan_content_hash,
                    review_confirmed=prepared.drawing_inputs.review_confirmed,
                    topic=prepared.drawing_inputs.topic,
                    drawing_steps=[
                        {"action": step.action, "placement": step.placement}
                        for step in prepared.drawing_inputs.drawing_steps
                    ],
                    subject_knowledge=list(prepared.drawing_inputs.subject_knowledge),
                    target_age_band=prepared.target_age_band,
                    deck_schema_version=DECK_SCHEMA_VERSION,
                    state="GENERATING",
                    model_profile_ref=model_profile_ref,
                    model_profile_version=model_profile_version,
                    prompt_template_version=PROMPT_TEMPLATE_VERSION,
                    config_hash=config_hash,
                    compute_reservation_ref=None,
                    content_hash=None,
                    created_by=access.account_ref,
                    created_at=now,
                    ready_at=None,
                    superseded_at=None,
                )
            )
            body = {
                "contract": "SketchDeckRevisionV1",
                "sketch_deck_revision_id": revision_id,
                "occurrence_id": prepared.occurrence_id,
                "plan_revision_id": prepared.plan_revision_id,
                "revision_no": revision_no,
                "plan_content_hash": prepared.plan_content_hash,
                "review_confirmed": prepared.drawing_inputs.review_confirmed,
                "topic": prepared.drawing_inputs.topic,
                "drawing_steps": [
                    {"action": step.action, "placement": step.placement}
                    for step in prepared.drawing_inputs.drawing_steps
                ],
                "subject_knowledge": list(prepared.drawing_inputs.subject_knowledge),
                "target_age_band": prepared.target_age_band,
                "deck_schema_version": DECK_SCHEMA_VERSION,
                "state": "GENERATING",
                "content_hash": None,
                "created_at": now.isoformat(),
                "ready_at": None,
                "superseded_at": None,
            }
            self.db.add(
                Be1CommandReceiptModel(
                    principal_ref=principal.subject,
                    operation_scope=scope,
                    idempotency_key=idempotency_key,
                    organization_id=str(access.occurrence["organization_ref"]),
                    request_fingerprint=fingerprint,
                    response_json=body,
                    response_status=202,
                )
            )
            self.db.commit()
            return SketchDeckGenerationStart(
                sketch_deck_revision_id=revision_id,
                revision_no=revision_no,
                occurrence_id=prepared.occurrence_id,
                plan_revision_id=prepared.plan_revision_id,
                plan_content_hash=prepared.plan_content_hash,
                target_age_band=prepared.target_age_band,
                plan_activity_ids=prepared.plan_activity_ids,
                drawing=prepared.drawing,
            )
        except IntegrityError as error:
            self.db.rollback()
            winner = self._receipt(principal, prepared.occurrence_id, idempotency_key)
            if winner is not None:
                return self._replay(winner, fingerprint)
            if getattr(error.orig, "sqlstate", None) == "23505":
                raise DocumentError(409, "STALE_REVISION") from None
            raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
        except SQLAlchemyError:
            self.db.rollback()
            raise DocumentError(503, "PROVIDER_UNAVAILABLE") from None
        except BaseException:
            self.db.rollback()
            raise

    def complete_generation(
        self,
        *,
        principal: VerifiedPrincipal,
        generation: SketchDeckGenerationStart,
        idempotency_key: str,
        deck: Mapping[str, Any],
    ) -> SketchDeckCommandResult:
        try:
            steps = _steps_from_worker(deck, generation.plan_activity_ids)
            drawing = generation.drawing or drawing_from_ai_draft(deck.get("drawing"))
            steps = attach_progressive_drawing(steps, drawing)
            steps = validate_ready_steps(generation.plan_activity_ids, steps)
        except SketchDeckRuleError:
            return self.fail_generation(
                principal=principal,
                generation=generation,
                idempotency_key=idempotency_key,
            )
        try:
            authorize_occurrence(
                self.db, principal, generation.occurrence_id, write=True, lock="update"
            )
            revision = self.db.execute(
                select(SKETCH_DECK_REVISIONS)
                .where(
                    SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id
                    == generation.sketch_deck_revision_id
                )
                .with_for_update()
            ).mappings().one_or_none()
            if revision is None or revision["state"] != "GENERATING":
                raise DocumentError(409, "INVALID_STATE_TRANSITION")
            newer_ready = self.db.scalar(
                select(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id)
                .where(
                    SKETCH_DECK_REVISIONS.c.occurrence_id == generation.occurrence_id,
                    SKETCH_DECK_REVISIONS.c.revision_no > revision["revision_no"],
                    SKETCH_DECK_REVISIONS.c.state == "READY",
                )
                .limit(1)
            )
            if newer_ready is not None:
                return self._fail_locked(
                    principal=principal,
                    generation=generation,
                    idempotency_key=idempotency_key,
                    rollback_first=False,
                )
            current_plan = self.db.execute(
                select(PLAN_REVISIONS.c.plan_revision_id, PLAN_REVISIONS.c.content_hash)
                .join(
                    OCCURRENCES,
                    OCCURRENCES.c.approved_plan_revision_id == PLAN_REVISIONS.c.plan_revision_id,
                )
                .where(OCCURRENCES.c.occurrence_id == generation.occurrence_id)
            ).one_or_none()
            if (
                current_plan is None
                or current_plan.plan_revision_id != generation.plan_revision_id
                or current_plan.content_hash != generation.plan_content_hash
            ):
                return self._fail_locked(
                    principal=principal,
                    generation=generation,
                    idempotency_key=idempotency_key,
                    rollback_first=False,
                )

            now = datetime.now(UTC)
            for old_id in self.db.scalars(
                select(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id).where(
                    SKETCH_DECK_REVISIONS.c.occurrence_id == generation.occurrence_id,
                    SKETCH_DECK_REVISIONS.c.state == "READY",
                )
            ).all():
                self.db.execute(
                    SKETCH_DECK_REVISIONS.update()
                    .where(SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id == old_id)
                    .values(state="SUPERSEDED", superseded_at=now)
                )
                self.db.execute(
                    SKETCH_DECK_STEPS.update()
                    .where(
                        SKETCH_DECK_STEPS.c.sketch_deck_revision_id == old_id,
                        SKETCH_DECK_STEPS.c.state == "READY",
                    )
                    .values(state="SUPERSEDED")
                )

            for step in steps:
                self.db.execute(
                    SKETCH_DECK_STEPS.insert().values(
                        sketch_deck_step_id=str(uuid4()),
                        sketch_deck_revision_id=generation.sketch_deck_revision_id,
                        plan_activity_id=step.plan_activity_id,
                        instruction_group_key=step.instruction_group_key,
                        step_index=step.step_index,
                        step_kind=step.step_kind,
                        subject_key=step.subject_key,
                        short_title=step.short_title,
                        child_facing_prompt=step.child_facing_prompt,
                        teacher_explanation=step.teacher_explanation,
                        bounded_layout_hints=dict(step.bounded_layout_hints),
                        line_sketch_asset_ref=step.line_sketch_asset_ref,
                        line_sketch_asset_version=step.line_sketch_asset_version,
                        source_job_ref=step.source_job_ref,
                        state="GENERATING",
                        created_at=now,
                    )
                )
            stored_inputs = SketchDeckDrawingInputs(
                review_confirmed=bool(revision["review_confirmed"]),
                topic=str(revision["topic"]),
                drawing_steps=tuple(
                    DrawingStepInput(str(step["action"]), str(step["placement"]))
                    for step in revision["drawing_steps"]
                ),
                subject_knowledge=tuple(str(note) for note in revision["subject_knowledge"]),
            )
            deck_hash = revision_content_hash(stored_inputs, steps)
            self.db.execute(
                SKETCH_DECK_REVISIONS.update()
                .where(
                    SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id
                    == generation.sketch_deck_revision_id
                )
                .values(state="READY", content_hash=deck_hash, ready_at=now)
            )
            self.db.execute(
                SKETCH_DECK_STEPS.update()
                .where(
                    SKETCH_DECK_STEPS.c.sketch_deck_revision_id
                    == generation.sketch_deck_revision_id
                )
                .values(state="READY")
            )
            body = self._revision_body(
                generation.sketch_deck_revision_id,
                state="READY",
                content_hash=deck_hash,
                ready_at=now,
                superseded_at=None,
            )
            self._finish_receipt(
                principal=principal,
                occurrence_id=generation.occurrence_id,
                idempotency_key=idempotency_key,
                body=body,
                status_code=201,
            )
            self.db.commit()
            return SketchDeckCommandResult(body, 201, False)
        except DocumentError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            return self.fail_generation(
                principal=principal,
                generation=generation,
                idempotency_key=idempotency_key,
            )
        except BaseException:
            self.db.rollback()
            raise

    def fail_generation(
        self,
        *,
        principal: VerifiedPrincipal,
        generation: SketchDeckGenerationStart,
        idempotency_key: str,
    ) -> SketchDeckCommandResult:
        return self._fail_locked(
            principal=principal,
            generation=generation,
            idempotency_key=idempotency_key,
            rollback_first=True,
        )

    def current(self, *, principal: VerifiedPrincipal, occurrence_id: str) -> dict[str, Any]:
        access = authorize_occurrence(self.db, principal, occurrence_id)
        revision = self.db.execute(
            select(SKETCH_DECK_REVISIONS)
            .where(SKETCH_DECK_REVISIONS.c.occurrence_id == occurrence_id)
            .order_by(SKETCH_DECK_REVISIONS.c.revision_no.desc())
            .limit(1)
        ).mappings().one_or_none()
        if revision is None:
            self.db.rollback()
            return {
                "contract": "SketchDeckCurrentV1",
                "occurrence_id": occurrence_id,
                "current_revision": None,
                "steps": [],
                "stale": False,
                "presentable": False,
            }
        plan_hash = self.db.scalar(
            select(PLAN_REVISIONS.c.content_hash).where(
                PLAN_REVISIONS.c.plan_revision_id == access.occurrence["approved_plan_revision_id"],
                PLAN_REVISIONS.c.state == "APPROVED",
            )
        )
        stale = bool(
            revision["state"] == "STALE"
            or revision["plan_revision_id"] != access.occurrence["approved_plan_revision_id"]
            or revision["plan_content_hash"] != plan_hash
        )
        presentable = bool(revision["state"] == "READY" and not stale)
        step_rows = self.db.execute(
            select(SKETCH_DECK_STEPS)
            .where(
                SKETCH_DECK_STEPS.c.sketch_deck_revision_id
                == revision["sketch_deck_revision_id"]
            )
            .order_by(
                SKETCH_DECK_STEPS.c.instruction_group_key,
                SKETCH_DECK_STEPS.c.step_index,
            )
        ).mappings().all()
        body = {
            "contract": "SketchDeckCurrentV1",
            "occurrence_id": occurrence_id,
            "current_revision": self._revision_body_from_row(revision),
            "steps": [self._step_body(row) for row in step_rows],
            "stale": stale,
            "presentable": presentable,
        }
        self.db.rollback()
        return body

    def _fail_locked(
        self,
        *,
        principal: VerifiedPrincipal,
        generation: SketchDeckGenerationStart,
        idempotency_key: str,
        rollback_first: bool,
    ) -> SketchDeckCommandResult:
        if rollback_first:
            self.db.rollback()
        try:
            authorize_occurrence(
                self.db, principal, generation.occurrence_id, write=True, lock="update"
            )
            row = self.db.execute(
                select(SKETCH_DECK_REVISIONS)
                .where(
                    SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id
                    == generation.sketch_deck_revision_id
                )
                .with_for_update()
            ).mappings().one_or_none()
            if row is None:
                raise DocumentError(404, "RESOURCE_NOT_FOUND")
            if row["state"] == "GENERATING":
                self.db.execute(
                    SKETCH_DECK_REVISIONS.update()
                    .where(
                        SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id
                        == generation.sketch_deck_revision_id
                    )
                    .values(state="FAILED")
                )
            body = self._revision_body(
                generation.sketch_deck_revision_id,
                state="FAILED",
                content_hash=None,
                ready_at=None,
                superseded_at=None,
            )
            self._finish_receipt(
                principal=principal,
                occurrence_id=generation.occurrence_id,
                idempotency_key=idempotency_key,
                body=body,
                status_code=201,
            )
            self.db.commit()
            return SketchDeckCommandResult(body, 201, False)
        except BaseException:
            self.db.rollback()
            raise

    def _approved_plan(
        self,
        *,
        occurrence: RowMapping,
        occurrence_id: str,
        expected_plan_revision_id: str,
        expected_plan_hash: str,
    ) -> RowMapping:
        plan = self.db.execute(
            select(PLAN_REVISIONS).where(
                PLAN_REVISIONS.c.plan_revision_id == expected_plan_revision_id,
                PLAN_REVISIONS.c.occurrence_id == occurrence_id,
            )
        ).mappings().one_or_none()
        if plan is None:
            raise not_found()
        if (
            occurrence["approved_plan_revision_id"] != expected_plan_revision_id
            or plan["state"] != "APPROVED"
            or plan["content_hash"] != expected_plan_hash
        ):
            raise DocumentError(409, "STALE_REVISION")
        return plan

    def _receipt(
        self, principal: VerifiedPrincipal, occurrence_id: str, key: str
    ) -> Be1CommandReceiptModel | None:
        scope = CREATE_RECEIPT_SCOPE.format(occurrence_id=occurrence_id)
        return self.db.get(Be1CommandReceiptModel, (principal.subject, scope, key))

    def _replay(
        self, receipt: Be1CommandReceiptModel, fingerprint: str
    ) -> SketchDeckCommandResult:
        if receipt.request_fingerprint != fingerprint:
            raise DocumentError(400, "INVALID_IDEMPOTENCY_KEY")
        body = dict(receipt.response_json)
        return SketchDeckCommandResult(body, int(receipt.response_status), True)

    def _finish_receipt(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        idempotency_key: str,
        body: dict[str, Any],
        status_code: int,
    ) -> None:
        receipt = self._receipt(principal, occurrence_id, idempotency_key)
        if receipt is None:
            raise DocumentError(503, "PROVIDER_UNAVAILABLE")
        receipt.response_json = _json_safe(body)
        receipt.response_status = status_code

    def _revision_body(
        self,
        revision_id: str,
        *,
        state: str,
        content_hash: str | None,
        ready_at: datetime | None,
        superseded_at: datetime | None,
    ) -> dict[str, Any]:
        row = self.db.execute(
            select(SKETCH_DECK_REVISIONS).where(
                SKETCH_DECK_REVISIONS.c.sketch_deck_revision_id == revision_id
            )
        ).mappings().one_or_none()
        if row is None:
            raise DocumentError(503, "PROVIDER_UNAVAILABLE")
        body = dict(self._revision_body_from_row(row))
        body.update(
            state=state,
            content_hash=content_hash,
            ready_at=ready_at,
            superseded_at=superseded_at,
        )
        return cast(dict[str, Any], _json_safe(body))

    @staticmethod
    def _revision_body_from_row(row: RowMapping) -> dict[str, Any]:
        return {
            "contract": "SketchDeckRevisionV1",
            "sketch_deck_revision_id": str(row["sketch_deck_revision_id"]),
            "occurrence_id": str(row["occurrence_id"]),
            "plan_revision_id": str(row["plan_revision_id"]),
            "revision_no": int(row["revision_no"]),
            "plan_content_hash": str(row["plan_content_hash"]),
            "review_confirmed": bool(row["review_confirmed"]),
            "topic": str(row["topic"]),
            "drawing_steps": [dict(step) for step in row["drawing_steps"]],
            "subject_knowledge": list(row["subject_knowledge"]),
            "target_age_band": str(row["target_age_band"]),
            "deck_schema_version": str(row["deck_schema_version"]),
            "state": str(row["state"]),
            "content_hash": row["content_hash"],
            "created_at": row["created_at"],
            "ready_at": row["ready_at"],
            "superseded_at": row["superseded_at"],
        }

    @staticmethod
    def _step_body(row: RowMapping) -> dict[str, Any]:
        return {
            "sketch_deck_step_id": str(row["sketch_deck_step_id"]),
            "plan_activity_id": row["plan_activity_id"],
            "instruction_group_key": str(row["instruction_group_key"]),
            "step_index": int(row["step_index"]),
            "step_kind": str(row["step_kind"]),
            "subject_key": str(row["subject_key"]),
            "short_title": str(row["short_title"]),
            "child_facing_prompt": str(row["child_facing_prompt"]),
            "teacher_explanation": str(row["teacher_explanation"]),
            "bounded_layout_hints": dict(row["bounded_layout_hints"]),
            "line_sketch_asset_ref": row["line_sketch_asset_ref"],
            "line_sketch_asset_version": row["line_sketch_asset_version"],
            "source_job_ref": row["source_job_ref"],
            "state": str(row["state"]),
            "created_at": row["created_at"],
        }


def _steps_from_worker(
    deck: Mapping[str, Any], plan_activity_ids: Sequence[str]
) -> tuple[SketchDeckStep, ...]:
    """Turn the worker's ``teacher-sketch-deck.v1`` slides into stored drawing steps.

    The worker returns one drawing guide for the whole deck, and READY needs every plan activity
    covered by a group of 4-8 steps (SRS SketchDeckStepV1), so each activity gets its own group
    with the guide's steps. Any other shape fails closed.
    """

    def refuse(field: str | None = None) -> SketchDeckRuleError:
        return SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", field)

    if deck.get("review_required") is not True:
        raise refuse()
    if deck.get("schema_version") != "sketch2life.teacher-sketch-deck.v1":
        raise refuse("schema_version")
    refs = deck.get("approved_activity_refs")
    if (
        not isinstance(refs, list)
        or any(not isinstance(ref, str) for ref in refs)
        or len(set(refs)) != len(refs)
        or set(refs) != set(plan_activity_ids)
    ):
        raise refuse("activity_ref")
    topic = deck.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise refuse("topic")
    slides = deck.get("slides")
    if not isinstance(slides, list) or any(not isinstance(slide, dict) for slide in slides):
        raise refuse("slides")
    guides = [slide for slide in slides if slide.get("kind") == "drawing_guide"]
    if len(guides) != 1:
        raise refuse("drawing_guide")
    rows = guides[0].get("steps")
    if not isinstance(rows, list) or not rows:
        raise refuse("steps")
    guide: list[tuple[str, str]] = []
    for expected_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("step_index") != expected_index:
            raise refuse("step_index")
        instruction = row.get("instruction")
        placement = row.get("placement")
        if not isinstance(instruction, str) or not isinstance(placement, str):
            raise refuse("steps")
        guide.append((instruction, placement))
    subject_key = topic.strip()[:80].strip()
    return tuple(
        SketchDeckStep(
            plan_activity_id=str(activity_id),
            instruction_group_key=f"guide:{activity_id}",
            step_index=index,
            step_kind="DRAWING_STEP",
            subject_key=subject_key,
            short_title=f"Bước {index}",
            child_facing_prompt=instruction,
            teacher_explanation=placement,
            bounded_layout_hints={"placement": placement},
            line_sketch_asset_ref=None,
            line_sketch_asset_version=None,
            source_job_ref=None,
        )
        for activity_id in plan_activity_ids
        for index, (instruction, placement) in enumerate(guide, start=1)
    )


def _bounded_text_segments(value: str, *, maximum: int = 240) -> list[str]:
    words = value.split()
    segments: list[str] = []
    current = ""
    for word in words:
        while len(word) > maximum:
            if current:
                segments.append(current)
                current = ""
            segments.append(word[:maximum])
            word = word[maximum:]
        candidate = f"{current} {word}".strip()
        if len(candidate) > maximum:
            segments.append(current)
            current = word
        else:
            current = candidate
    if current:
        segments.append(current)
    if not 1 <= len(segments) <= 8:
        raise DocumentError(409, "SKETCH_DECK_PLAN_INCOMPLETE")
    return segments


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


__all__ = [
    "CREATE_RECEIPT_SCOPE",
    "DECK_SCHEMA_VERSION",
    "MODEL_CONFIG_VERSION",
    "PROMPT_TEMPLATE_VERSION",
    "WORKER_INPUT_SCHEMA_VERSION",
    "PreparedSketchDeck",
    "SketchDeckCommandResult",
    "SketchDeckGenerationStart",
    "SketchDeckRevisionService",
]
