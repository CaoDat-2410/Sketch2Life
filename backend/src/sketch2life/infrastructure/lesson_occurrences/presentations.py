"""Teacher presentation application service (SRS FR-T-19..22; T-SLD1)."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.presentation_svg import (
    PresentationSvgDrafter,
    PresentationSvgDrafterUnavailable,
    PresentationSvgDraftInput,
)
from sketch2life.application.ports.upload_sessions import ORGANIZATION_SCOPE
from sketch2life.contracts.schemas.svg_engine import SvgDocumentV1
from sketch2life.domain.lesson_occurrences.presentation import (
    PresentationRuleError,
    apply_operations,
    command_fingerprint,
    content_hash,
    embed_url,
    media_state,
    stale_reasons,
    validate_subject_text,
)
from sketch2life.domain.lesson_occurrences.presentation import (
    etag as presentation_etag,
)
from sketch2life.infrastructure.lesson_occurrences.scope import (
    LessonOccurrenceError,
    OccurrenceAccess,
    authorize_occurrence,
    require_class_writable,
)
from sketch2life.infrastructure.lesson_occurrences.tables import (
    PLAN_ACTIVITIES,
    PLAN_REVISIONS,
    PRESENTATION_REVISIONS,
    PRESENTATION_SVG_DRAFTS,
    PRESENTATIONS,
)
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.svg_catalog_tables import (
    SVG_CATALOG_ASSETS,
    SVG_CATALOG_REVIEWS,
)
from sketch2life.infrastructure.story_inputs.drawing import (
    DrawingNormalizationError,
    normalize_drawing,
)
from sketch2life.infrastructure.story_inputs.service import read_verified_original
from sketch2life.infrastructure.svg.renderer import render_svg_document
from sketch2life.infrastructure.svg.sanitizer import sanitize_svg_source
from sketch2life.infrastructure.uploads.purposes import (
    IMAGE_EXTENSIONS,
    MAX_IMAGE_BYTES,
    PRESENTATION_IMAGE,
)
from sketch2life.infrastructure.uploads.service import CompletedUpload, resolve_completed_upload

# SQLAlchemy RowMapping keys are not plain str, so row inputs use a key-agnostic mapping.
_Row = Mapping[Any, Any]

CREATE_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/presentation"
REVISION_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/presentation/revisions"
READY_SCOPE = (
    "POST /v1/lesson-occurrences/{occurrence_id}/presentation/revisions/{revision_no}/ready"
)
SVG_CREATE_SCOPE = "POST /v1/lesson-occurrences/{occurrence_id}/presentation/svg-drafts"
SVG_DECISION_SCOPE = (
    "POST /v1/lesson-occurrences/{occurrence_id}/presentation/svg-drafts/"
    "{svg_draft_id}/decision"
)
SVG_DRAFTS_PER_24H = 20
ALLOWED_GENERATED_LICENSES = frozenset({"CC0-1.0"})
_READ_CHUNK_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class PresentationCommandResult:
    body: dict[str, Any]
    status_code: int
    etag: str
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class PresentationImageResult:
    body: bytes
    media_type: str
    sha256: str


@dataclass(frozen=True, slots=True)
class _PreparedPresentationImage:
    upload: CompletedUpload
    width: int
    height: int


class _RateLimitedLessonOccurrenceError(LessonOccurrenceError):
    retry_after: int

    def __init__(self, retry_after: int) -> None:
        super().__init__(429, "RATE_LIMITED")
        self.retry_after = retry_after


def _operation_scope(route_template: str, **path_ids: str) -> str:
    scope = route_template
    for name, value in path_ids.items():
        scope = scope.replace("{" + name + "}", value)
    if "{" in scope or "}" in scope or len(scope) > 256:
        raise ValueError("receipt scope is not a bounded, fully bound route")
    return scope


def _json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _db_unavailable() -> LessonOccurrenceError:
    return LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE")


class LessonPresentationService:
    def __init__(
        self,
        db: Session,
        *,
        storage: ObjectStoragePort | None,
        svg_drafter: PresentationSvgDrafter | None,
    ) -> None:
        self.db = db
        self.storage = storage
        self.svg_drafter = svg_drafter

    # ------------------------------------------------------------- authorization/receipts
    def _access(
        self,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        *,
        write: bool,
        lock: bool = False,
    ) -> OccurrenceAccess:
        access = authorize_occurrence(
            self.db,
            principal,
            occurrence_id,
            write=write,
            lock="update" if lock else None,
        )
        if write:
            if access.occurrence["state"] == "ARCHIVED":
                raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
            require_class_writable(self.db, access.occurrence, lock=lock)
        return access

    def _presentation(self, occurrence_id: str, *, lock: bool = False) -> _Row | None:
        statement = select(PRESENTATIONS).where(PRESENTATIONS.c.occurrence_id == occurrence_id)
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).mappings().one_or_none()

    def _receipt(
        self, principal: VerifiedPrincipal, scope: str, key: str, *, lock: bool = True
    ) -> Be1CommandReceiptModel | None:
        statement = select(Be1CommandReceiptModel).where(
            Be1CommandReceiptModel.principal_ref == principal.subject,
            Be1CommandReceiptModel.operation_scope == scope,
            Be1CommandReceiptModel.idempotency_key == key,
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.execute(statement).scalar_one_or_none()

    def _replay(
        self,
        receipt: Be1CommandReceiptModel,
        fingerprint: str,
        status_code: int,
    ) -> PresentationCommandResult:
        if receipt.request_fingerprint != fingerprint:
            raise LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY")
        response_json = receipt.response_json
        body = response_json.get("body") if isinstance(response_json, dict) else None
        etag_value = response_json.get("etag") if isinstance(response_json, dict) else None
        if not isinstance(body, dict) or not isinstance(etag_value, str):
            raise _db_unavailable()
        return PresentationCommandResult(dict(body), status_code, etag_value, True)

    @staticmethod
    def _receipt_race(error: IntegrityError) -> bool:
        original = getattr(error, "orig", None)
        diagnostic = getattr(original, "diag", None)
        return (
            getattr(original, "sqlstate", None) == "23505"
            and getattr(diagnostic, "constraint_name", None) == "pk_be1_command_receipts"
        )

    def _race_replay(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        presentation_id: str | None,
        draft_id: str | None,
        scope: str,
        key: str,
        fingerprint: str,
        status_code: int,
        draft_ids: Sequence[str] = (),
    ) -> PresentationCommandResult:
        self._access(principal, occurrence_id, write=True, lock=True)
        if presentation_id is not None:
            self._presentation(occurrence_id, lock=True)
        locked_draft_ids = set(draft_ids)
        if draft_id is not None:
            locked_draft_ids.add(draft_id)
        if locked_draft_ids:
            statement = select(PRESENTATION_SVG_DRAFTS.c.svg_draft_id).where(
                PRESENTATION_SVG_DRAFTS.c.svg_draft_id.in_(sorted(locked_draft_ids))
            )
            if presentation_id is not None:
                statement = statement.where(
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id
                )
            self.db.execute(
                statement.order_by(PRESENTATION_SVG_DRAFTS.c.svg_draft_id).with_for_update()
            ).all()
        receipt = self._receipt(principal, scope, key)
        if receipt is None:
            self.db.rollback()
            raise LessonOccurrenceError(409, "RESOURCE_CONFLICT")
        try:
            result = self._replay(receipt, fingerprint, status_code)
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        self.db.rollback()
        return result

    def _finish(
        self,
        *,
        principal: VerifiedPrincipal,
        account_ref: str,
        organization_id: str,
        occurrence_id: str,
        presentation_id: str | None,
        draft_id: str | None,
        scope: str,
        key: str,
        fingerprint: str,
        body: dict[str, Any],
        status_code: int,
        etag_value: str,
        action: str,
        resource_type: str,
        resource_id: str,
        draft_ids: Sequence[str] = (),
    ) -> PresentationCommandResult:
        self.db.add(
            CoreAuditEntryModel(
                audit_id=str(uuid4()),
                organization_id=organization_id,
                owner_scope_kind="ORGANIZATION",
                owner_scope_ref=None,
                actor_ref=account_ref,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                decision="allowed",
            )
        )
        self.db.add(
            Be1CommandReceiptModel(
                principal_ref=principal.subject,
                operation_scope=scope,
                idempotency_key=key,
                organization_id=organization_id,
                request_fingerprint=fingerprint,
                response_json={"body": _json_safe(body), "etag": etag_value},
            )
        )
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if self._receipt_race(exc):
                try:
                    return self._race_replay(
                        principal=principal,
                        occurrence_id=occurrence_id,
                        presentation_id=presentation_id,
                        draft_id=draft_id,
                        scope=scope,
                        key=key,
                        fingerprint=fingerprint,
                        status_code=status_code,
                        draft_ids=draft_ids,
                    )
                except SQLAlchemyError:
                    self.db.rollback()
                    raise _db_unavailable() from None
            raise LessonOccurrenceError(409, "RESOURCE_CONFLICT") from None
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None
        return PresentationCommandResult(body, status_code, etag_value)

    # ------------------------------------------------------------------------- plans/revisions
    def _current_plan(self, occurrence: _Row) -> _Row:
        plan_id = occurrence["approved_plan_revision_id"]
        if not plan_id:
            raise LessonOccurrenceError(409, "LESSON_PLAN_NOT_APPROVED")
        plan = self.db.execute(
            select(PLAN_REVISIONS).where(
                PLAN_REVISIONS.c.plan_revision_id == plan_id,
                PLAN_REVISIONS.c.occurrence_id == occurrence["occurrence_id"],
                PLAN_REVISIONS.c.state == "APPROVED",
            )
        ).mappings().one_or_none()
        if plan is None:
            raise LessonOccurrenceError(409, "LESSON_PLAN_NOT_APPROVED")
        return plan

    def _plan_activities(self, plan_id: str) -> list[_Row]:
        return list(
            self.db.execute(
                select(PLAN_ACTIVITIES)
                .where(PLAN_ACTIVITIES.c.plan_revision_id == plan_id)
                .order_by(PLAN_ACTIVITIES.c.activity_order)
            ).mappings().all()
        )

    def _insert_revision(
        self,
        *,
        presentation_id: str,
        revision_no: int,
        base_revision_no: int | None,
        plan: _Row,
        slides: list[dict[str, Any]],
        actor_ref: str,
    ) -> None:
        self.db.execute(
            PRESENTATION_REVISIONS.insert().values(
                presentation_revision_id=str(uuid4()),
                presentation_id=presentation_id,
                revision_no=revision_no,
                base_revision_no=base_revision_no,
                plan_revision_id=plan["plan_revision_id"],
                plan_content_hash=plan["content_hash"],
                content_hash=content_hash(slides),
                slides=slides,
                state="DRAFT",
                created_by=actor_ref,
            )
        )

    def _revision_row(self, presentation_id: str, revision_no: int) -> _Row | None:
        return self.db.execute(
            select(PRESENTATION_REVISIONS).where(
                PRESENTATION_REVISIONS.c.presentation_id == presentation_id,
                PRESENTATION_REVISIONS.c.revision_no == revision_no,
            )
        ).mappings().one_or_none()

    def _lock_svg_drafts(self, presentation_id: str, draft_ids: Sequence[str]) -> None:
        unique_ids = sorted({draft_id for draft_id in draft_ids if draft_id})
        if unique_ids:
            self.db.execute(
                select(PRESENTATION_SVG_DRAFTS.c.svg_draft_id)
                .where(
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id,
                    PRESENTATION_SVG_DRAFTS.c.svg_draft_id.in_(unique_ids),
                )
                .order_by(PRESENTATION_SVG_DRAFTS.c.svg_draft_id)
                .with_for_update()
            ).all()

    def _media_state_maps(
        self,
        slides: Sequence[_Row],
    ) -> tuple[dict[str, str], dict[str, str]]:
        catalog_ids: set[str] = set()
        draft_ids: set[str] = set()
        for slide in slides:
            media = slide.get("media")
            if not isinstance(media, Mapping):
                continue
            if media.get("kind") == "SVG_CATALOG" and media.get("catalog_entry_id"):
                catalog_ids.add(str(media["catalog_entry_id"]))
            if media.get("kind") == "SVG_AI" and media.get("svg_draft_id"):
                draft_ids.add(str(media["svg_draft_id"]))
        catalogs: dict[str, str] = {}
        drafts: dict[str, str] = {}
        if catalog_ids:
            catalogs = {
                str(row["catalog_entry_id"]): str(row["catalog_state"])
                for row in self.db.execute(
                    select(
                        SVG_CATALOG_ASSETS.c.catalog_entry_id,
                        SVG_CATALOG_ASSETS.c.catalog_state,
                    ).where(SVG_CATALOG_ASSETS.c.catalog_entry_id.in_(sorted(catalog_ids)))
                ).mappings()
            }
        if draft_ids:
            drafts = {
                str(row["svg_draft_id"]): str(row["state"])
                for row in self.db.execute(
                    select(
                        PRESENTATION_SVG_DRAFTS.c.svg_draft_id,
                        PRESENTATION_SVG_DRAFTS.c.state,
                    ).where(PRESENTATION_SVG_DRAFTS.c.svg_draft_id.in_(sorted(draft_ids)))
                ).mappings()
            }
        return catalogs, drafts

    def _public_slide(
        self,
        slide: _Row,
        catalogs: Mapping[str, str],
        drafts: Mapping[str, str],
    ) -> dict[str, Any]:
        raw_media = slide.get("media")
        public_media: dict[str, Any] | None = None
        state = media_state(raw_media, catalog_states=catalogs, draft_states=drafts)
        if isinstance(raw_media, Mapping):
            kind = raw_media.get("kind")
            placement = raw_media.get("placement", "FULL")
            alt_text = raw_media.get("alt_text", "")
            if kind == "IMAGE":
                public_media = {
                    "kind": kind,
                    "asset_ref": "upl_" + str(raw_media.get("upload_id", "")),
                    "alt_text": alt_text,
                    "media_type": raw_media.get("media_type", "image/png"),
                    "width": raw_media.get("width", 1),
                    "height": raw_media.get("height", 1),
                    "placement": placement,
                }
            elif kind == "SVG_CATALOG":
                public_media = {
                    "kind": kind,
                    "catalog_entry_id": raw_media.get("catalog_entry_id"),
                    "alt_text": alt_text,
                    "canonical_sha256": raw_media.get("canonical_sha256"),
                    "placement": placement,
                }
            elif kind == "SVG_AI":
                public_media = {
                    "kind": kind,
                    "svg_draft_id": raw_media.get("svg_draft_id"),
                    "alt_text": alt_text,
                    "canonical_sha256": raw_media.get("canonical_sha256"),
                    "placement": placement,
                }
            elif kind == "VIDEO_EMBED":
                public_media = {
                    "kind": kind,
                    "provider": raw_media.get("provider"),
                    "video_id": raw_media.get("video_id"),
                    "embed_url": embed_url(
                        str(raw_media.get("provider")),
                        str(raw_media.get("video_id")),
                    ),
                    "placement": placement,
                }
        return {
            "slide_id": slide["slide_id"],
            "position": int(slide["position"]),
            "title": slide["title"],
            "body_text": slide["body_text"],
            "media": public_media,
            "media_state": state,
        }

    def _revision_body(
        self,
        row: _Row,
        *,
        current_plan_revision_id: str | None,
    ) -> dict[str, Any]:
        slides = row["slides"] if isinstance(row["slides"], list) else []
        catalogs, drafts = self._media_state_maps(slides)
        reasons = stale_reasons(
            pinned_plan_revision_id=str(row["plan_revision_id"]),
            current_plan_revision_id=current_plan_revision_id,
            slides=slides,
            catalog_states=catalogs,
            draft_states=drafts,
        )
        plan = self.db.execute(
            select(PLAN_REVISIONS.c.revision_no).where(
                PLAN_REVISIONS.c.plan_revision_id == row["plan_revision_id"]
            )
        ).scalar_one_or_none()
        if plan is None:
            raise _db_unavailable()
        return {
            "contract": "LessonPresentationRevisionV1",
            "revision_no": int(row["revision_no"]),
            "base_revision_no": row["base_revision_no"],
            "state": row["state"],
            "aspect_ratio": "16:9",
            "source_state": "STALE" if reasons else "CURRENT",
            "stale_reasons": reasons,
            "plan_revision_no": int(plan),
            "plan_content_hash": row["plan_content_hash"],
            "content_hash": row["content_hash"],
            "slides": [self._public_slide(slide, catalogs, drafts) for slide in slides],
            "created_at": row["created_at"],
            "readied_at": row["readied_at"],
        }

    def _aggregate_body(
        self,
        presentation: _Row,
        occurrence: _Row,
    ) -> dict[str, Any]:
        head = self._revision_row(
            str(presentation["presentation_id"]),
            int(presentation["head_revision_no"]),
        )
        if head is None:
            raise _db_unavailable()
        current_plan_id = occurrence["approved_plan_revision_id"]
        current_plan_ref = None if current_plan_id is None else str(current_plan_id)
        ready_no = presentation["ready_revision_no"]
        basis = head
        if ready_no is not None:
            ready = self._revision_row(str(presentation["presentation_id"]), int(ready_no))
            if ready is None:
                raise _db_unavailable()
            basis = ready
        basis_slides = basis["slides"] if isinstance(basis["slides"], list) else []
        catalogs, drafts = self._media_state_maps(basis_slides)
        reasons = stale_reasons(
            pinned_plan_revision_id=str(basis["plan_revision_id"]),
            current_plan_revision_id=None if current_plan_id is None else str(current_plan_id),
            slides=basis_slides,
            catalog_states=catalogs,
            draft_states=drafts,
        )
        return {
            "contract": "LessonPresentationV1",
            "presentation_id": presentation["presentation_id"],
            "occurrence_id": presentation["occurrence_id"],
            "revision": int(presentation["revision"]),
            "head_revision_no": int(presentation["head_revision_no"]),
            "ready_revision_no": None if ready_no is None else int(ready_no),
            "source_state": "STALE" if reasons else "CURRENT",
            "stale_reasons": reasons,
            "presentable": ready_no is not None and not reasons,
            "head": self._revision_body(
                head, current_plan_revision_id=current_plan_ref
            ),
        }

    # ------------------------------------------------------------------------------- commands
    def create(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, seed: str, idempotency_key: str
    ) -> PresentationCommandResult:
        fingerprint = command_fingerprint(
            method="POST", route=CREATE_SCOPE, ids={"occurrence_id": occurrence_id},
            if_match=None, body={"seed": seed},
        )
        try:
            self._access(principal, occurrence_id, write=True)
            receipt_scope = _operation_scope(CREATE_SCOPE, occurrence_id=occurrence_id)
            access = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence = access.occurrence
            existing = self._presentation(occurrence_id, lock=True)
            receipt = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt:
                result = self._replay(receipt, fingerprint, 201)
                self.db.rollback()
                return result
            if existing is not None:
                raise LessonOccurrenceError(409, "RESOURCE_CONFLICT")
            plan = self._current_plan(occurrence)
            rows = self._plan_activities(str(plan["plan_revision_id"]))
            activities = [
                {
                    "title": (
                        row["custom_title"]
                        if row["activity_kind"] == "CUSTOM"
                        else (row["activity_snapshot"] or {}).get("title")
                    ),
                    "description": (
                        row["custom_description"]
                        if row["activity_kind"] == "CUSTOM"
                        else (row["activity_snapshot"] or {}).get("instructions_text")
                    ),
                }
                for row in rows
            ]
            slides = self._seed_slides(activities, seed)
            presentation_id = str(uuid4())
            now = datetime.now(UTC)
            self.db.execute(
                PRESENTATIONS.insert().values(
                    presentation_id=presentation_id,
                    occurrence_id=occurrence_id,
                    organization_ref=occurrence["organization_ref"],
                    head_revision_no=1,
                    ready_revision_no=None,
                    revision=1,
                    created_by=access.account_ref,
                    created_at=now,
                    updated_at=now,
                )
            )
            self._insert_revision(
                presentation_id=presentation_id, revision_no=1, base_revision_no=None,
                plan=plan, slides=slides, actor_ref=access.account_ref,
            )
            self.db.flush()
            presentation = self._presentation(occurrence_id)
            assert presentation is not None
            body = self._aggregate_body(presentation, occurrence)
            return self._finish(
                principal=principal, account_ref=access.account_ref,
                organization_id=str(occurrence["organization_ref"]), occurrence_id=occurrence_id,
                presentation_id=presentation_id, draft_id=None, scope=receipt_scope,
                key=idempotency_key, fingerprint=fingerprint, body=body, status_code=201,
                etag_value=presentation_etag(1), action="lesson.presentation.create",
                resource_type="lesson_presentation", resource_id=presentation_id,
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    @staticmethod
    def _seed_slides(activities: Sequence[_Row], seed: str) -> list[dict[str, Any]]:
        from sketch2life.domain.lesson_occurrences.presentation import seed_slides

        cleaned = [
            {"title": item.get("title") or "", "description": item.get("description") or ""}
            for item in activities
        ]
        try:
            return seed_slides(cleaned, seed=seed)
        except PresentationRuleError as exc:
            raise LessonOccurrenceError(
                400,
                "INVALID_REQUEST",
                field_errors=[{"field": exc.field or "seed", "code": exc.code}],
            ) from None

    def create_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        expected_revision: int,
        if_match: str,
        idempotency_key: str,
        repin_to_current_plan: bool,
        operations: Sequence[_Row],
    ) -> PresentationCommandResult:
        request_body = {
            "repin_to_current_plan": repin_to_current_plan,
            "operations": list(operations),
        }
        fingerprint = command_fingerprint(
            method="POST", route=REVISION_SCOPE, ids={"occurrence_id": occurrence_id},
            if_match=if_match, body=request_body,
        )
        try:
            if not 1 <= len(operations) <= 50:
                raise LessonOccurrenceError(
                    400,
                    "INVALID_REQUEST",
                    field_errors=[{"field": "operations", "code": "OUT_OF_RANGE"}],
                )
            preflight_access = self._access(principal, occurrence_id, write=True)
            receipt_scope = _operation_scope(REVISION_SCOPE, occurrence_id=occurrence_id)
            prior_receipt = self._receipt(
                principal, receipt_scope, idempotency_key, lock=False
            )
            if prior_receipt:
                result = self._replay(prior_receipt, fingerprint, 201)
                self.db.rollback()
                return result
            image_uploads = self._collect_image_uploads(
                occurrence=preflight_access.occurrence,
                operations=operations,
            )
            self.db.rollback()
            prepared_images = self._prepare_image_uploads(image_uploads)

            access = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence = access.occurrence
            presentation = self._presentation(occurrence_id, lock=True)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            presentation_id = str(presentation["presentation_id"])
            draft_ids = [
                str(media["svg_draft_id"])
                for operation in operations
                if operation.get("op") == "SET_MEDIA"
                and isinstance((media := operation.get("media")), Mapping)
                and media.get("kind") == "SVG_AI"
                and media.get("svg_draft_id")
            ]
            self._lock_svg_drafts(presentation_id, draft_ids)
            receipt = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt:
                result = self._replay(receipt, fingerprint, 201)
                self.db.rollback()
                return result
            if int(presentation["revision"]) != expected_revision:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(presentation["revision"]),
                )
            current_plan = self._current_plan(occurrence)
            head = self._revision_row(
                str(presentation["presentation_id"]),
                int(presentation["head_revision_no"]),
            )
            if head is None:
                raise _db_unavailable()
            pinned_plan: _Row = current_plan
            if not repin_to_current_plan:
                fetched_plan = self.db.execute(
                    select(PLAN_REVISIONS).where(
                        PLAN_REVISIONS.c.plan_revision_id == head["plan_revision_id"],
                        PLAN_REVISIONS.c.state == "APPROVED",
                    )
                ).mappings().one_or_none()
                if fetched_plan is None:
                    raise LessonOccurrenceError(409, "STALE_SOURCE_VERSION")
                pinned_plan = fetched_plan
            slides: list[dict[str, Any]] = head["slides"]
            for index, operation in enumerate(operations):
                if operation.get("op") == "SET_MEDIA" and not any(
                    slide.get("slide_id") == operation.get("slide_id") for slide in slides
                ):
                    raise LessonOccurrenceError(
                        400,
                        "INVALID_REQUEST",
                        field_errors=[
                            {
                                "field": f"operations[{index}].slide_id",
                                "code": "INVALID_FORMAT",
                            }
                        ],
                    )
                resolved_operation = self._resolve_media_operations(
                    occurrence=occurrence,
                    presentation_id=presentation_id,
                    operations=[operation],
                    prepared_images=prepared_images,
                )
                try:
                    slides = apply_operations(
                        slides, resolved_operation, operation_index_offset=index
                    )
                except PresentationRuleError as exc:
                    raise LessonOccurrenceError(
                        400,
                        "INVALID_REQUEST",
                        field_errors=[
                            {
                                "field": exc.field or f"operations[{index}]",
                                "code": exc.code,
                            }
                        ],
                    ) from None
            next_revision_no = int(presentation["head_revision_no"]) + 1
            self._validate_catalog_slides(
                slides, str(occurrence["organization_ref"])
            )
            self._insert_revision(
                presentation_id=str(presentation["presentation_id"]), revision_no=next_revision_no,
                base_revision_no=int(presentation["head_revision_no"]), plan=pinned_plan,
                slides=slides, actor_ref=access.account_ref,
            )
            update_result = self.db.execute(
                update(PRESENTATIONS)
                .where(
                    PRESENTATIONS.c.presentation_id == presentation["presentation_id"],
                    PRESENTATIONS.c.revision == expected_revision,
                )
                .values(
                    head_revision_no=next_revision_no,
                    revision=expected_revision + 1,
                    updated_at=func.now(),
                )
            )
            if cast("CursorResult[Any]", update_result).rowcount != 1:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(presentation["revision"]),
                )
            self.db.flush()
            changed = self._presentation(occurrence_id)
            assert changed is not None
            body = self._aggregate_body(changed, occurrence)
            return self._finish(
                principal=principal,
                account_ref=access.account_ref,
                organization_id=str(occurrence["organization_ref"]),
                occurrence_id=occurrence_id,
                presentation_id=presentation_id,
                draft_id=None,
                draft_ids=draft_ids,
                scope=receipt_scope,
                key=idempotency_key,
                fingerprint=fingerprint,
                body=body,
                status_code=201,
                etag_value=presentation_etag(expected_revision + 1),
                action="lesson.presentation.revision.create",
                resource_type="lesson_presentation_revision",
                resource_id=f"{presentation['presentation_id']}:{next_revision_no}",
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    def _resolve_media_operations(
        self,
        *,
        occurrence: _Row,
        presentation_id: str,
        operations: Sequence[_Row],
        prepared_images: Mapping[str, _PreparedPresentationImage],
    ) -> list[dict[str, Any]]:
        resolved: list[dict[str, Any]] = []
        for raw in operations:
            operation = dict(raw)
            if operation.get("op") == "SET_MEDIA":
                media = dict(operation.get("media") or {})
                kind = media.get("kind")
                if kind == "IMAGE":
                    media.update(
                        self._validate_image_metadata(
                            occurrence=occurrence,
                            media=media,
                            prepared_images=prepared_images,
                        )
                    )
                elif kind == "SVG_CATALOG":
                    entry = self._catalog_entry(
                        str(media.get("catalog_entry_id", "")),
                        str(occurrence["organization_ref"]),
                    )
                    media["canonical_sha256"] = str(entry["canonical_sha256"])
                elif kind == "SVG_AI":
                    draft = self.db.execute(
                        select(PRESENTATION_SVG_DRAFTS).where(
                            PRESENTATION_SVG_DRAFTS.c.svg_draft_id == media.get("svg_draft_id"),
                            PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id,
                        )
                    ).mappings().one_or_none()
                    if draft is None:
                        raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
                    if draft["state"] != "ACCEPTED":
                        raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
                    media["canonical_sha256"] = str(draft["canonical_sha256"])
                operation["media"] = media
            resolved.append(operation)
        return resolved

    def _catalog_entry(self, entry_id: str, organization_id: str) -> _Row:
        row = self.db.execute(
            select(SVG_CATALOG_ASSETS).where(
                SVG_CATALOG_ASSETS.c.catalog_entry_id == entry_id
            )
        ).mappings().one_or_none()
        if row is None or not (
            row["visibility_scope"] == "PLATFORM"
            or (
                row["visibility_scope"] == "ORGANIZATION"
                and row["organization_id"] == organization_id
            )
        ):
            raise LessonOccurrenceError(404, "SVG_CATALOG_NOT_AVAILABLE")
        return row

    def _latest_catalog_source_review(
        self, entry: _Row, review_kind: str
    ) -> str | None:
        return self.db.execute(
            select(SVG_CATALOG_REVIEWS.c.decision)
            .where(
                SVG_CATALOG_REVIEWS.c.asset_ref == entry["asset_ref"],
                SVG_CATALOG_REVIEWS.c.asset_version == entry["asset_version"],
                SVG_CATALOG_REVIEWS.c.review_subject_kind == "SOURCE_ASSET",
                SVG_CATALOG_REVIEWS.c.review_kind == review_kind,
                SVG_CATALOG_REVIEWS.c.source_sha256 == entry["source_sha256"],
                SVG_CATALOG_REVIEWS.c.guide_revision_id.is_(None),
            )
            .order_by(
                SVG_CATALOG_REVIEWS.c.created_at.desc(),
                SVG_CATALOG_REVIEWS.c.review_id.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()

    def _validate_catalog_svg_media(
        self, media: Mapping[str, Any], organization_id: str
    ) -> None:
        entry = self._catalog_entry(
            str(media.get("catalog_entry_id", "")), organization_id
        )
        if entry["catalog_state"] == "REJECTED":
            raise LessonOccurrenceError(409, "SVG_CATALOG_REJECTED")
        if entry["catalog_state"] == "ARCHIVED":
            raise LessonOccurrenceError(404, "SVG_CATALOG_NOT_AVAILABLE")
        if entry["catalog_state"] != "ACTIVE":
            raise LessonOccurrenceError(409, "SVG_CATALOG_NOT_APPROVED")

        pinned_hash = media.get("canonical_sha256")
        current_hash = str(entry["canonical_sha256"])
        if not isinstance(pinned_hash, str) or pinned_hash.lower() != current_hash.lower():
            raise LessonOccurrenceError(409, "SVG_CATALOG_HASH_MISMATCH")

        educator_decision = self._latest_catalog_source_review(entry, "EDUCATOR")
        if educator_decision == "REJECT":
            raise LessonOccurrenceError(409, "SVG_CATALOG_REJECTED")
        if educator_decision != "APPROVE":
            raise LessonOccurrenceError(409, "SVG_CATALOG_NOT_APPROVED")
        if entry["visibility_scope"] == "PLATFORM":
            curator_decision = self._latest_catalog_source_review(entry, "CURATOR")
            if curator_decision == "REJECT":
                raise LessonOccurrenceError(409, "SVG_CATALOG_REJECTED")
            if curator_decision != "APPROVE":
                raise LessonOccurrenceError(409, "SVG_CATALOG_NOT_APPROVED")

    def _validate_catalog_slides(
        self, slides: Sequence[_Row], organization_id: str
    ) -> None:
        for slide in slides:
            media = slide.get("media")
            if isinstance(media, Mapping) and media.get("kind") == "SVG_CATALOG":
                self._validate_catalog_svg_media(media, organization_id)

    def _resolve_presentation_upload(
        self, occurrence: _Row, asset_ref: str
    ) -> CompletedUpload:
        upload = resolve_completed_upload(
            self.db,
            asset_ref,
            purpose=PRESENTATION_IMAGE,
            owner_scope_kind=ORGANIZATION_SCOPE,
            owner_scope_ref=None,
            organization_id=str(occurrence["organization_ref"]),
            target_ref=str(occurrence["occurrence_id"]),
        )
        if upload is None:
            raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
        if upload.size_bytes > MAX_IMAGE_BYTES:
            raise LessonOccurrenceError(413, "MEDIA_TOO_LARGE")
        if upload.media_type not in IMAGE_EXTENSIONS:
            raise LessonOccurrenceError(415, "UNSUPPORTED_MEDIA_TYPE")
        return upload

    def _collect_image_uploads(
        self,
        *,
        occurrence: _Row,
        operations: Sequence[_Row],
    ) -> dict[str, CompletedUpload]:
        uploads: dict[str, CompletedUpload] = {}
        for operation in operations:
            if operation.get("op") != "SET_MEDIA":
                continue
            media = operation.get("media")
            if not isinstance(media, Mapping) or media.get("kind") != "IMAGE":
                continue
            upload = self._resolve_presentation_upload(
                occurrence, str(media.get("asset_ref", ""))
            )
            uploads.setdefault(upload.upload_id, upload)
        return uploads

    def _prepare_image_uploads(
        self, uploads: Mapping[str, CompletedUpload]
    ) -> dict[str, _PreparedPresentationImage]:
        if uploads and self.storage is None:
            raise LessonOccurrenceError(503, "STORAGE_UNAVAILABLE")
        prepared: dict[str, _PreparedPresentationImage] = {}
        for upload_id, upload in uploads.items():
            assert self.storage is not None
            try:
                source = read_verified_original(
                    self.storage,
                    upload.asset_key,
                    upload.size_bytes,
                    upload.sha256,
                )
            except ParentStoryRunError as exc:
                raise LessonOccurrenceError(exc.status_code, exc.code) from None
            try:
                normalized = normalize_drawing(source, declared_media_type=upload.media_type)
            except DrawingNormalizationError as exc:
                raise LessonOccurrenceError(exc.status_code, exc.code) from None
            prepared[upload_id] = _PreparedPresentationImage(
                upload=upload,
                width=normalized.source_width,
                height=normalized.source_height,
            )
        return prepared

    def _validate_image_metadata(
        self,
        *,
        occurrence: _Row,
        media: _Row,
        prepared_images: Mapping[str, _PreparedPresentationImage],
    ) -> dict[str, Any]:
        upload = self._resolve_presentation_upload(
            occurrence, str(media.get("asset_ref", ""))
        )
        prepared = prepared_images.get(upload.upload_id)
        if prepared is None or prepared.upload != upload:
            raise LessonOccurrenceError(409, "MEDIA_SOURCE_CHANGED")
        return {
            "media_type": upload.media_type,
            "width": prepared.width,
            "height": prepared.height,
        }

    def mark_ready(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        revision_no: int,
        expected_revision: int,
        if_match: str,
        idempotency_key: str,
    ) -> PresentationCommandResult:
        fingerprint = command_fingerprint(
            method="POST", route=READY_SCOPE,
            ids={"occurrence_id": occurrence_id, "revision_no": str(revision_no)},
            if_match=if_match, body=None,
        )
        try:
            self._access(principal, occurrence_id, write=True)
            receipt_scope = _operation_scope(
                READY_SCOPE,
                occurrence_id=occurrence_id,
                revision_no=str(revision_no),
            )
            access = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence = access.occurrence
            presentation = self._presentation(occurrence_id, lock=True)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            target = self._revision_row(str(presentation["presentation_id"]), revision_no)
            if target is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            slides = target["slides"] if isinstance(target["slides"], list) else []
            draft_ids = [
                str(slide["media"]["svg_draft_id"])
                for slide in slides
                if isinstance(slide, Mapping)
                and isinstance(slide.get("media"), Mapping)
                and slide["media"].get("kind") == "SVG_AI"
                and slide["media"].get("svg_draft_id")
            ]
            self._lock_svg_drafts(str(presentation["presentation_id"]), draft_ids)
            receipt = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt:
                result = self._replay(receipt, fingerprint, 200)
                self.db.rollback()
                return result
            if int(presentation["revision"]) != expected_revision:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(presentation["revision"]),
                )
            if int(presentation["head_revision_no"]) != revision_no:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(presentation["revision"]),
                )
            if target["state"] != "DRAFT":
                raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
            current_plan = self._current_plan(occurrence)
            self._validate_catalog_slides(
                slides, str(occurrence["organization_ref"])
            )
            catalogs, drafts = self._media_state_maps(slides)
            reasons = stale_reasons(
                pinned_plan_revision_id=str(target["plan_revision_id"]),
                current_plan_revision_id=str(current_plan["plan_revision_id"]),
                slides=slides,
                catalog_states=catalogs,
                draft_states=drafts,
            )
            if reasons:
                raise LessonOccurrenceError(409, "STALE_SOURCE_VERSION")
            now = datetime.now(UTC)
            if presentation["ready_revision_no"] is not None:
                previous = self._revision_row(
                    str(presentation["presentation_id"]), int(presentation["ready_revision_no"])
                )
                if previous is None:
                    raise _db_unavailable()
                self.db.execute(
                    update(PRESENTATION_REVISIONS)
                    .where(
                        PRESENTATION_REVISIONS.c.presentation_revision_id
                        == previous["presentation_revision_id"]
                    )
                    .values(state="SUPERSEDED", superseded_at=now)
                )
            self.db.execute(
                update(PRESENTATION_REVISIONS)
                .where(
                    PRESENTATION_REVISIONS.c.presentation_revision_id
                    == target["presentation_revision_id"]
                )
                .values(state="READY", readied_by=access.account_ref, readied_at=now)
            )
            update_result = self.db.execute(
                update(PRESENTATIONS)
                .where(
                    PRESENTATIONS.c.presentation_id == presentation["presentation_id"],
                    PRESENTATIONS.c.revision == expected_revision,
                )
                .values(
                    ready_revision_no=revision_no,
                    revision=expected_revision + 1,
                    updated_at=func.now(),
                )
            )
            if cast("CursorResult[Any]", update_result).rowcount != 1:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(presentation["revision"]),
                )
            self.db.flush()
            changed = self._presentation(occurrence_id)
            assert changed is not None
            body = self._aggregate_body(changed, occurrence)
            return self._finish(
                principal=principal,
                account_ref=access.account_ref,
                organization_id=str(occurrence["organization_ref"]),
                occurrence_id=occurrence_id,
                presentation_id=str(presentation["presentation_id"]),
                draft_id=None,
                draft_ids=draft_ids,
                scope=receipt_scope,
                key=idempotency_key,
                fingerprint=fingerprint,
                body=body,
                status_code=200,
                etag_value=presentation_etag(expected_revision + 1),
                action="lesson.presentation.revision.ready",
                resource_type="lesson_presentation_revision",
                resource_id=f"{presentation['presentation_id']}:{revision_no}",
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    # ---------------------------------------------------------------------------------- reads
    def get_presentation(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
    ) -> dict[str, Any]:
        try:
            access = self._access(principal, occurrence_id, write=False)
            presentation = self._presentation(occurrence_id)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            return self._aggregate_body(presentation, access.occurrence)
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    def get_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        revision_no: int,
    ) -> dict[str, Any]:
        try:
            access = self._access(principal, occurrence_id, write=False)
            presentation = self._presentation(occurrence_id)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            row = self._revision_row(str(presentation["presentation_id"]), revision_no)
            if row is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            current_plan_id = access.occurrence["approved_plan_revision_id"]
            return self._revision_body(
                row,
                current_plan_revision_id=(
                    None if current_plan_id is None else str(current_plan_id)
                ),
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    def get_image(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, asset_ref: str
    ) -> PresentationImageResult:
        try:
            access = self._access(principal, occurrence_id, write=False)
            presentation = self._presentation(occurrence_id)
            if presentation is None or not asset_ref.startswith("upl_"):
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            upload_id = asset_ref[4:]
            found = self.db.execute(
                select(PRESENTATION_REVISIONS.c.presentation_revision_id)
                .where(
                    PRESENTATION_REVISIONS.c.presentation_id == presentation["presentation_id"],
                    PRESENTATION_REVISIONS.c.slides.contains(
                        [{"media": {"kind": "IMAGE", "upload_id": upload_id}}]
                    )
                )
                .limit(1)
            ).first()
            if found is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            upload = resolve_completed_upload(
                self.db,
                asset_ref,
                purpose=PRESENTATION_IMAGE,
                owner_scope_kind=ORGANIZATION_SCOPE,
                owner_scope_ref=None,
                organization_id=str(access.occurrence["organization_ref"]),
                target_ref=occurrence_id,
            )
            if upload is None or self.storage is None:
                if self.storage is None and upload is not None:
                    raise LessonOccurrenceError(503, "STORAGE_UNAVAILABLE")
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            try:
                body = read_verified_original(
                    self.storage,
                    upload.asset_key,
                    upload.size_bytes,
                    upload.sha256,
                )
            except ParentStoryRunError as exc:
                raise LessonOccurrenceError(exc.status_code, exc.code) from None
            return PresentationImageResult(
                body, upload.media_type, hashlib.sha256(body).hexdigest()
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    # ----------------------------------------------------------------------------- SVG drafts
    def create_svg_draft(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        plan_activity_id: str,
        subject_text: str,
        idempotency_key: str,
    ) -> PresentationCommandResult:
        fingerprint: str
        normalized_subject: str
        # Transaction 1 reads and authorizes only. The drafter is invoked after rollback.
        try:
            self._access(principal, occurrence_id, write=True)
            receipt_scope = _operation_scope(SVG_CREATE_SCOPE, occurrence_id=occurrence_id)
            access = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence = access.occurrence
            presentation = self._presentation(occurrence_id, lock=True)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            try:
                normalized_subject = validate_subject_text(subject_text)
            except PresentationRuleError as exc:
                raise LessonOccurrenceError(
                    400,
                    "INVALID_REQUEST",
                    field_errors=[{"field": exc.field or "subject_text", "code": exc.code}],
                ) from None
            fingerprint = command_fingerprint(
                method="POST", route=SVG_CREATE_SCOPE,
                ids={"occurrence_id": occurrence_id}, if_match=None,
                body={"plan_activity_id": plan_activity_id, "subject_text": normalized_subject},
            )
            receipt = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt:
                replayed = self._replay(receipt, fingerprint, 201)
                self.db.rollback()
                return replayed
            drafter = self.svg_drafter
            if drafter is None:
                raise LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE")
            plan = self._current_plan(occurrence)
            activity = self.db.execute(
                select(
                    PLAN_ACTIVITIES.c.custom_title,
                    PLAN_ACTIVITIES.c.activity_kind,
                    PLAN_ACTIVITIES.c.activity_snapshot,
                )
                .where(
                    PLAN_ACTIVITIES.c.plan_revision_id == plan["plan_revision_id"],
                    PLAN_ACTIVITIES.c.plan_activity_id == plan_activity_id,
                )
            ).mappings().one_or_none()
            if activity is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            snapshot = (
                activity["activity_snapshot"]
                if isinstance(activity["activity_snapshot"], dict)
                else {}
            )
            activity_title = (
                activity["custom_title"]
                if activity["activity_kind"] == "CUSTOM"
                else snapshot.get("title")
            )
            if not isinstance(activity_title, str) or len(activity_title) > 160:
                raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
            count = self._svg_draft_count(str(presentation["presentation_id"]))
            if count >= SVG_DRAFTS_PER_24H:
                raise _RateLimitedLessonOccurrenceError(3600)
            presentation_id = str(presentation["presentation_id"])
            plan_id = str(plan["plan_revision_id"])
            self.db.rollback()
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

        draft_input = PresentationSvgDraftInput(
            schema_version="sketch2life.presentation-svg-input.v1",
            activity_title=activity_title,
            subject_text=normalized_subject,
        )
        try:
            generated = drafter.draft(draft_input)
            sanitized = sanitize_svg_source(generated.source)
            if sanitized.readiness.get("classification") not in {
                "REQUIRES_MANUAL_AUTHORING",
                "STROKE_READY",
            }:
                raise ValueError("sanitized SVG is not eligible for Teacher review")
            document = SvgDocumentV1.model_validate(sanitized.document).model_dump(mode="json")
            preview = render_svg_document(document)
            if (
                generated.license_id not in ALLOWED_GENERATED_LICENSES
                or not generated.generator_name
                or len(generated.generator_name) > 64
                or not generated.generator_version
                or len(generated.generator_version) > 128
            ):
                raise ValueError("provenance or license rejected")
        except PresentationSvgDrafterUnavailable:
            raise LessonOccurrenceError(503, "PROVIDER_UNAVAILABLE") from None
        except Exception:
            raise LessonOccurrenceError(502, "PROVIDER_BAD_RESPONSE") from None
        input_hash = content_hash(
            {
                "schema_version": draft_input.schema_version,
                "activity_title": activity_title,
                "subject_text": normalized_subject,
            }
        )
        svg_draft_id = str(uuid4())
        # Transaction 2 rechecks scope/plan/cap, then stores hashes, SVG and provenance.
        try:
            self._access(principal, occurrence_id, write=True)
            access2 = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence2 = access2.occurrence
            presentation2 = self._presentation(occurrence_id, lock=True)
            if presentation2 is None or str(presentation2["presentation_id"]) != presentation_id:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            receipt2 = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt2:
                replayed = self._replay(receipt2, fingerprint, 201)
                self.db.rollback()
                return replayed
            plan2 = self._current_plan(occurrence2)
            if str(plan2["plan_revision_id"]) != plan_id:
                raise LessonOccurrenceError(409, "STALE_SOURCE_VERSION")
            if self._svg_draft_count(presentation_id) >= SVG_DRAFTS_PER_24H:
                raise _RateLimitedLessonOccurrenceError(3600)
            self.db.execute(
                PRESENTATION_SVG_DRAFTS.insert().values(
                    svg_draft_id=svg_draft_id,
                    presentation_id=presentation_id,
                    state="PENDING_REVIEW",
                    revision=1,
                    input_hash=input_hash,
                    source_sha256=sanitized.source_sha256,
                    canonical_sha256=sanitized.canonical_sha256,
                    document=document,
                    sanitizer_version=sanitized.sanitizer_version,
                    generator_name=generated.generator_name,
                    generator_version=generated.generator_version,
                    license_id=generated.license_id,
                    created_by=access2.account_ref,
                )
            )
            self.db.flush()
            draft_row = self.db.execute(
                select(PRESENTATION_SVG_DRAFTS).where(
                    PRESENTATION_SVG_DRAFTS.c.svg_draft_id == svg_draft_id
                )
            ).mappings().one()
            body = self._draft_body(draft_row, preview_svg=preview)
            result = self._finish(
                principal=principal, account_ref=access2.account_ref,
                organization_id=str(occurrence2["organization_ref"]), occurrence_id=occurrence_id,
                presentation_id=presentation_id, draft_id=svg_draft_id, scope=receipt_scope,
                key=idempotency_key, fingerprint=fingerprint, body=body, status_code=201,
                etag_value=presentation_etag(1), action="lesson.presentation.svg_draft.create",
                resource_type="lesson_presentation_svg_draft", resource_id=svg_draft_id,
            )
            return result
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    def _svg_draft_count(self, presentation_id: str) -> int:
        since = datetime.now(UTC) - timedelta(hours=24)
        return int(
            self.db.execute(
                select(func.count())
                .select_from(PRESENTATION_SVG_DRAFTS)
                .where(
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation_id,
                    PRESENTATION_SVG_DRAFTS.c.created_at >= since,
                )
            ).scalar_one()
        )

    def _draft_body(
        self,
        row: _Row,
        *,
        preview_svg: str | None = None,
    ) -> dict[str, Any]:
        document = SvgDocumentV1.model_validate(row["document"]).model_dump(mode="json")
        preview = preview_svg if preview_svg is not None else render_svg_document(document)
        return {
            "contract": "PresentationSvgDraftV1",
            "svg_draft_id": row["svg_draft_id"],
            "state": row["state"],
            "revision": int(row["revision"]),
            "document": document,
            "preview_svg": preview,
            "canonical_sha256": row["canonical_sha256"],
            "generator": {"name": row["generator_name"], "version": row["generator_version"]},
            "license_id": row["license_id"],
            "created_at": row["created_at"],
            "decided_at": row["decided_at"],
        }

    def get_svg_draft(
        self, *, principal: VerifiedPrincipal, occurrence_id: str, svg_draft_id: str
    ) -> dict[str, Any]:
        try:
            self._access(principal, occurrence_id, write=False)
            presentation = self._presentation(occurrence_id)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            row = self.db.execute(
                select(PRESENTATION_SVG_DRAFTS).where(
                    PRESENTATION_SVG_DRAFTS.c.svg_draft_id == svg_draft_id,
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation["presentation_id"],
                )
            ).mappings().one_or_none()
            if row is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            return self._draft_body(row)
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None

    def decide_svg_draft(
        self,
        *,
        principal: VerifiedPrincipal,
        occurrence_id: str,
        svg_draft_id: str,
        expected_revision: int,
        if_match: str,
        decision: str,
        idempotency_key: str,
    ) -> PresentationCommandResult:
        fingerprint = command_fingerprint(
            method="POST", route=SVG_DECISION_SCOPE,
            ids={"occurrence_id": occurrence_id, "svg_draft_id": svg_draft_id},
            if_match=if_match, body={"decision": decision},
        )
        try:
            self._access(principal, occurrence_id, write=True)
            receipt_scope = _operation_scope(
                SVG_DECISION_SCOPE,
                occurrence_id=occurrence_id,
                svg_draft_id=svg_draft_id,
            )
            access = self._access(principal, occurrence_id, write=True, lock=True)
            occurrence = access.occurrence
            presentation = self._presentation(occurrence_id, lock=True)
            if presentation is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            draft = self.db.execute(
                select(PRESENTATION_SVG_DRAFTS)
                .where(
                    PRESENTATION_SVG_DRAFTS.c.svg_draft_id == svg_draft_id,
                    PRESENTATION_SVG_DRAFTS.c.presentation_id == presentation["presentation_id"],
                )
                .with_for_update()
            ).mappings().one_or_none()
            if draft is None:
                raise LessonOccurrenceError(404, "RESOURCE_NOT_FOUND")
            receipt = self._receipt(principal, receipt_scope, idempotency_key)
            if receipt:
                replayed = self._replay(receipt, fingerprint, 200)
                self.db.rollback()
                return replayed
            if int(draft["revision"]) != expected_revision:
                raise LessonOccurrenceError(
                    409,
                    "STALE_REVISION",
                    current_version=int(draft["revision"]),
                )
            if draft["state"] != "PENDING_REVIEW":
                raise LessonOccurrenceError(409, "INVALID_STATE_TRANSITION")
            next_state = "ACCEPTED" if decision == "ACCEPT" else "DISCARDED"
            decided_at = datetime.now(UTC)
            self.db.execute(
                update(PRESENTATION_SVG_DRAFTS)
                .where(PRESENTATION_SVG_DRAFTS.c.svg_draft_id == svg_draft_id)
                .values(
                    state=next_state,
                    revision=expected_revision + 1,
                    decided_by=access.account_ref,
                    decided_at=decided_at,
                )
            )
            body = self._draft_body(
                {
                    **dict(draft),
                    "state": next_state,
                    "revision": expected_revision + 1,
                    "decided_at": decided_at,
                }
            )
            return self._finish(
                principal=principal,
                account_ref=access.account_ref,
                organization_id=str(occurrence["organization_ref"]),
                occurrence_id=occurrence_id,
                presentation_id=str(presentation["presentation_id"]),
                draft_id=svg_draft_id,
                scope=receipt_scope,
                key=idempotency_key,
                fingerprint=fingerprint,
                body=body,
                status_code=200,
                etag_value=presentation_etag(expected_revision + 1),
                action="lesson.presentation.svg_draft.decide",
                resource_type="lesson_presentation_svg_draft",
                resource_id=svg_draft_id,
            )
        except LessonOccurrenceError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise _db_unavailable() from None


__all__ = ["LessonPresentationService", "PresentationCommandResult", "PresentationImageResult"]
