"""``POST /v1/story-runs``: one route, two bodies, dispatched by the caller's role (T-4b2 D1).

SRS l.1663 gives the route to "Parent hoặc Teacher" with the scope matching the role. The Parent
function, its signature, its ``response_model`` and every answer a Parent, a Manager, a Platform
Admin or an unauthenticated caller gets stay exactly as they were: ``RoleDispatchedCreateRoute``
wraps the unchanged Parent handler and sends a request to the Teacher endpoint only when the body is
Teacher-shaped (a JSON object with a Teacher key) AND the caller is an active Teacher with a
matching
issuer. For every other caller the Teacher endpoint steps aside (``_FallThroughToParent``) and the
Parent handler answers the same request, so a Teacher-shaped body from a non-Teacher gets today's
400 or 404 byte for byte. A Teacher who sends a Parent-shaped body reaches the Parent handler and
gets today's uniform 404 (OWNER-VISIBLE, OPEN-7: the role cannot be known before the shape is).

The Teacher endpoint declares no body and no header parameter: it reads the body the wrapper already
parsed, so FastAPI cannot raise its own validation error before the role is known (R2 N-6). Its
validation errors are raised as ``RequestValidationError`` with ``loc`` starting ``("body", ...)``,
the shape FastAPI itself produces, so the application's one handler formats them.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import ValidationError
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.responses import Response as StarletteResponse

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    TeacherStoryRunRecord,
)
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryRunLifecycleEnvelopeV1,
)
from sketch2life.contracts.schemas.story_run_video import (
    ParentStoryRunVideoV1,
    ParentStoryTimelineEventV1,
)
from sketch2life.contracts.schemas.teacher_story_runs import (
    TeacherActiveStoryRunEnvelopeV1,
    TeacherRunActivityV1,
    TeacherRunPlanV1,
    TeacherRunProfileRefV1,
    TeacherStoryRunCreateRequestV1,
    TeacherStoryRunEnvelopeV1,
    TeacherStoryRunResponseV1,
)
from sketch2life.domain.story_teacher import (
    is_teacher_shaped,
    multi_child_requested,
    parse_json_object,
)
from sketch2life.infrastructure.lesson_occurrences.child_selection import (
    synthetic_gate_from_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.teacher_run_access import SqlTeacherRunAccess
from sketch2life.infrastructure.story_teacher.repository import TeacherStoryRunCreator
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    get_db,
    get_runtime,
    get_verified_adult,
)

STORY_RUNS_PATH = "/v1/story-runs"
PARENT_REQUEST_REF = "#/components/schemas/ParentStoryRunCreateRequestV1"
_JSON_MEDIA = "application/json"

Handler = Callable[[Request], Coroutine[Any, Any, StarletteResponse]]


class _FallThroughToParent(Exception):
    """The caller is not an active Teacher: the Parent handler answers this request."""


# ----------------------------------------------------------------------------- views
def teacher_story_run_response(record: TeacherStoryRunRecord) -> TeacherStoryRunResponseV1:
    """The one builder of the Teacher run view (``StoryRunDetailV1`` for a Teacher, D10)."""

    return TeacherStoryRunResponseV1(
        run_id=UUID(record.run_id),
        run_revision=record.run_revision,
        run_state=record.run_state,  # type: ignore[arg-type]
        profile_ref=TeacherRunProfileRefV1(id=record.profile_ref),
        profile_revision_ref=record.profile_revision_ref,
        occurrence_id=record.occurrence_id,
        plan=TeacherRunPlanV1.model_validate(record.plan) if record.plan is not None else None,
        activity=(
            TeacherRunActivityV1.model_validate(record.activity)
            if record.activity is not None
            else None
        ),
        context_revision=record.context_revision,
        context_confirmed=record.context_confirmed,
        context_snapshot=record.context_snapshot,  # type: ignore[arg-type]
        context_snapshot_sha256=record.context_snapshot_sha256,
        lesson_pin_snapshot=record.lesson_pin_snapshot,  # type: ignore[arg-type]
        current_input_revision=record.current_input_revision,
        understanding_revision=record.understanding_revision,
        subject_label=record.subject_label,
        candidate=record.candidate,  # type: ignore[arg-type]
        story_revision_id=(
            UUID(record.story_revision_id) if record.story_revision_id is not None else None
        ),
        story_revision_no=record.story_revision_no,
        story_status=record.story_status,  # type: ignore[arg-type]
        story_sha256=record.story_sha256,
        story=record.story_content,  # type: ignore[arg-type]
        job_state=record.job_state,  # type: ignore[arg-type]
        retryable=record.retryable,
        error_code=record.error_code,
        created_at=record.created_at,
        updated_at=record.updated_at,
        video=(
            ParentStoryRunVideoV1.model_validate(record.video) if record.video is not None else None
        ),
        timeline=[ParentStoryTimelineEventV1.model_validate(event) for event in record.timeline],
        story_confirmation_required=record.story_confirmation_required,
    )


def teacher_envelope(record: TeacherStoryRunRecord) -> TeacherStoryRunEnvelopeV1:
    return TeacherStoryRunEnvelopeV1(
        request_id=uuid4(), story_run=teacher_story_run_response(record)
    )


def teacher_active_envelope(
    record: TeacherStoryRunRecord | None,
) -> TeacherActiveStoryRunEnvelopeV1:
    return TeacherActiveStoryRunEnvelopeV1(
        request_id=uuid4(),
        story_run=teacher_story_run_response(record) if record is not None else None,
    )


# ----------------------------------------------------------------------------- the endpoint
def get_teacher_story_run_creator(
    db: Session = Depends(get_db),  # noqa: B008
    runtime: Be1Runtime = Depends(get_runtime),  # noqa: B008
) -> TeacherStoryRunCreator:
    """The synthetic gate comes from the runtime settings: a REAL child is never created for
    (X-19); outside local and test the gate is off and no selection can be confirmed."""

    return TeacherStoryRunCreator(db, gate=synthetic_gate_from_settings(runtime.settings))


def _call[ResultT](callable_: Callable[..., ResultT], **kwargs: Any) -> ResultT:
    """Run one repository call; a refusal becomes the story envelope's HTTP error."""

    try:
        return callable_(**kwargs)
    except ParentStoryRunError as exc:
        detail: dict[str, Any] = {"code": exc.code}
        if exc.current_version is not None:
            detail["current_version"] = exc.current_version
        if exc.field_errors:
            detail["field_errors"] = exc.field_errors
        raise HTTPException(status_code=exc.status_code, detail=detail) from None


def _body_errors(error: ValidationError) -> list[Any]:
    """The pydantic errors with ``loc`` starting ``("body", ...)``, as FastAPI produces them."""

    return [{**item, "loc": ("body", *item["loc"])} for item in error.errors()]


def create_teacher_story_run(
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    creator: TeacherStoryRunCreator = Depends(get_teacher_story_run_creator),  # noqa: B008
) -> Any:
    """``POST /v1/story-runs`` for an active Teacher (SRS l.1445-1449, l.1663)."""

    identity = db.get(AdultIdentityModel, principal.subject)
    if (
        identity is None
        or identity.state != "active"
        or identity.account_role != "teacher"
        or identity.issuer != principal.issuer
    ):
        raise _FallThroughToParent
    data: dict[str, Any] = request.state.teacher_create_body
    if multi_child_requested(data):
        # SRS l.870, l.1449, l.1723: one child per run, never an array.
        raise HTTPException(status_code=422, detail={"code": "MULTI_CHILD_NOT_SUPPORTED"})
    try:
        body = TeacherStoryRunCreateRequestV1.model_validate(data)
    except ValidationError as exc:
        raise RequestValidationError(_body_errors(exc)) from None
    key = parse_idempotency_key(request)
    outcome = _call(creator.create, principal=principal, body=body, idempotency_key=key)
    actor = RunActor(kind=RunActorKind.TEACHER, account_id=identity.account_id)
    repository = SqlParentStoryRunRepository(
        db, actor=actor, teacher_access=SqlTeacherRunAccess(db)
    )
    record = _call(repository.get_run, principal=principal, run_id=outcome.run_id)
    if isinstance(record, ParentStoryLifecycleRecord):
        # A replay of a run that is pending deletion or deleted answers the lifecycle projection,
        # as the Parent create does (DTR 6.5 A-3).
        projection = ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": record.as_body()}
        )
        return JSONResponse(status_code=201, content=projection.model_dump(mode="json"))
    assert isinstance(record, TeacherStoryRunRecord)
    response.status_code = 201
    response.headers["Location"] = f"{STORY_RUNS_PATH}/{outcome.run_id}"
    return teacher_envelope(record)


# ----------------------------------------------------------------------------- the route class
def _json_media(request: Request) -> bool:
    """The rule FastAPI applies to decide that the body is JSON (no header means JSON)."""

    content_type = request.headers.get("content-type")
    if not content_type:
        return True
    media = content_type.split(";", 1)[0].strip().lower()
    return media == _JSON_MEDIA or (media.startswith("application/") and media.endswith("+json"))


class RoleDispatchedCreateRoute(APIRoute):
    """The Parent create route, plus a Teacher branch that only an active Teacher can enter."""

    def __init__(self, path: str, endpoint: Callable[..., Any], **kwargs: Any) -> None:
        # The hidden Teacher route first: the base constructor builds the handler through
        # ``get_route_handler``, which needs it. It is never mounted and never published.
        self._teacher_route = APIRoute(
            path,
            endpoint=create_teacher_story_run,
            methods=["POST"],
            response_model=TeacherStoryRunEnvelopeV1,
            status_code=201,
            include_in_schema=False,
        )
        super().__init__(path, endpoint, **kwargs)

    def get_route_handler(self) -> Handler:
        parent_handler = super().get_route_handler()

        async def handler(request: Request) -> StarletteResponse:
            raw = await request.body()
            data = parse_json_object(raw) if _json_media(request) else None
            if is_teacher_shaped(data):
                request.state.teacher_create_body = data
                # FastAPI includes a router lazily, so the hidden route never learns the
                # application: its overrides provider is the application of this request.
                self._teacher_route.dependency_overrides_provider = request.app
                try:
                    return await self._teacher_route.get_route_handler()(request)
                except _FallThroughToParent:
                    pass
            return await parent_handler(request)

        return handler


# ----------------------------------------------------------------------------- OpenAPI
def _component(components: dict[str, Any], name: str, model: type[Any], mode: str) -> None:
    """Add ``model`` and the models it uses to ``components.schemas`` when they are missing."""

    if name in components:
        return
    schema = model.model_json_schema(ref_template="#/components/schemas/{model}", mode=mode)
    for def_name, definition in schema.pop("$defs", {}).items():
        components.setdefault(def_name, definition)
    components[name] = schema


def publish_teacher_story_run_create(schema: dict[str, Any]) -> None:
    """Make the document of ``POST /v1/story-runs`` valid for both bodies (R2 N-2).

    The Parent request schema and the Parent responses are kept as they are; the request body
    becomes a proper ``oneOf`` of the Parent and the Teacher schema (disjoint: both forbid extra
    keys and their required keys differ), the 201 answer gains the Teacher envelope, and the
    Teacher schemas are registered so that no ``$ref`` dangles.
    """

    operation = schema.get("paths", {}).get(STORY_RUNS_PATH, {}).get("post")
    if not isinstance(operation, dict):
        return
    body_schema = (
        operation.get("requestBody", {}).get("content", {}).get(_JSON_MEDIA, {}).get("schema")
    )
    if body_schema != {"$ref": PARENT_REQUEST_REF}:
        return  # not the Parent create (the loopback demo replaces the route): nothing to add
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    _component(
        components, "TeacherStoryRunCreateRequestV1", TeacherStoryRunCreateRequestV1, "validation"
    )
    _component(components, "TeacherStoryRunEnvelopeV1", TeacherStoryRunEnvelopeV1, "serialization")
    teacher_ref = {"$ref": "#/components/schemas/TeacherStoryRunCreateRequestV1"}
    operation["requestBody"]["content"][_JSON_MEDIA]["schema"] = {
        "oneOf": [{"$ref": PARENT_REQUEST_REF}, teacher_ref]
    }
    created = operation.get("responses", {}).get("201", {}).get("content", {}).get(_JSON_MEDIA)
    if isinstance(created, dict) and isinstance(created.get("schema"), dict):
        parent_response = created["schema"]
        teacher_response = {"$ref": "#/components/schemas/TeacherStoryRunEnvelopeV1"}
        members = parent_response.get("anyOf")
        if isinstance(members, list):
            if teacher_response not in members:
                members.append(teacher_response)
        else:
            created["schema"] = {"anyOf": [parent_response, teacher_response]}


__all__ = [
    "RoleDispatchedCreateRoute",
    "create_teacher_story_run",
    "get_teacher_story_run_creator",
    "publish_teacher_story_run_create",
    "teacher_active_envelope",
    "teacher_envelope",
    "teacher_story_run_response",
]
