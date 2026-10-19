"""Injected CMD-45 only; no default production auth/mount or competing BE1 routes."""

from collections.abc import Callable
from dataclasses import replace
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from sketch2life.application.activity_execution import ActivityExecutionService, Command, Result
from sketch2life.application.ports.activity_execution import Actor
from sketch2life.contracts.schemas.activity_execution import ActivityAssignmentView, ActivityCommand
from sketch2life.domain.activity_execution.model import (
    TERMINAL,
    Action,
    Adaptations,
    Confirmation,
    effective,
    fail,
)
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity
from sketch2life.interfaces.http.routers.video_review import (
    _body,
    _error,
    _InputError,
    _key,
    _revision,
)

_CODES = {
    "ACTIVITY_FORBIDDEN": 403,
    "ACTIVITY_SCOPE_MISMATCH": 403,
    "ACTIVITY_NOT_FOUND": 404,
    "ACTIVITY_STALE_REVISION": 409,
    "ACTIVITY_SOURCE_MISMATCH": 409,
    "ACTIVITY_SOURCE_INELIGIBLE": 409,
    "ACTIVITY_POLICY_DENIED": 409,
    "ACTIVITY_INVALID_TRANSITION": 409,
    "ACTIVITY_NOT_READY": 409,
    "ACTIVITY_PREPARATION_STALE": 409,
    "ACTIVITY_IDEMPOTENCY_CONFLICT": 409,
    "ACTIVITY_WRITE_CONFLICT": 409,
    "ACTIVITY_DEPENDENCY_UNAVAILABLE": 503,
}


def build_activity_execution_router(
    service: ActivityExecutionService | None,
    resolve_identity: Callable[[Request], VideoIdentity | None],
    *,
    max_body_bytes: int,
    prefix: str = "/api/collaboration/v1",
) -> APIRouter:
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("explicit positive max_body_bytes required")
    router = APIRouter(prefix=prefix, tags=["activity-execution-candidate"])

    @router.post("/activity-assignments", response_model=None)
    async def execute(request: Request) -> Response:
        correlation = "corr_" + uuid4().hex
        try:
            if len(request.headers.getlist("authorization")) > 1:
                raise _InputError(401, "UNAUTHENTICATED")
            verified = await run_in_threadpool(resolve_identity, request)
            if verified is None:
                raise _InputError(401, "UNAUTHENTICATED")
            if type(verified) is not VideoIdentity:
                raise RuntimeError("invalid identity adapter")
            verified = replace(verified)
            key = _key(request)
            raw = await _body(request, max_body_bytes)
            try:
                body = ActivityCommand.model_validate_json(raw, strict=True)
                expected = None
                if body.assignment_id is not None:
                    expected = _revision(request)
                elif request.headers.getlist("if-match"):
                    raise _InputError(400, "ACTIVITY_CREATE_PRECONDITION_FORBIDDEN")
                if (
                    body.audience_scope is not None
                    and body.audience_scope.session_id != verified.session_id
                ):
                    fail("SCOPE_MISMATCH")
                cmd = Command(
                    Action(body.action),
                    body.assignment_id,
                    expected,
                    None
                    if body.activity_ref is None
                    else ExactRef(
                        body.activity_ref.activity_id,
                        body.activity_ref.version,
                        body.activity_ref.hash,
                    ),
                    None if body.audience_scope is None else body.audience_scope.group_ids,
                    None
                    if body.teacher_adaptations is None
                    else Adaptations(**body.teacher_adaptations.model_dump(mode="python")),
                    None
                    if body.feasibility_confirmation is None
                    else Confirmation(**body.feasibility_confirmation.model_dump(mode="python")),
                    body.reason,
                    tuple(ExactRef(r.ref, r.version, r.hash) for r in body.evidence_refs),
                )
            except VideoError:
                raise
            except ValueError:
                raise _InputError(422, "ACTIVITY_INVALID_COMMAND") from None
            if service is None:
                raise RuntimeError("unconfigured service")
            actor = Actor(verified.principal_id, verified.organization_id, verified.session_id, key)
            result = await run_in_threadpool(service.execute, actor, cmd)
            try:
                if type(result) is not Result:
                    raise ValueError("result")
                row = replace(result.assignment)
                if (
                    (row.organization_id, row.audience.session_id)
                    != (actor.organization_id, actor.session_id)
                    or type(result.replayed) is not bool
                    or type(result.applied_revision) is not int
                    or (
                        result.applied_revision < 1
                        or result.applied_revision > row.revision
                        or (not result.replayed and result.applied_revision != row.revision)
                        or (
                            cmd.assignment_id is not None and cmd.assignment_id != row.assignment_id
                        )
                        or ((row.state in TERMINAL) != (result.outcome_delivery != "not_required"))
                    )
                ):
                    raise ValueError("foreign result")
                snapshot = effective(row.source, row.edits)
                view = ActivityAssignmentView.model_validate(
                    {
                        "assignment_id": row.assignment_id,
                        "assignment_revision": row.revision,
                        "applied_revision": result.applied_revision,
                        "replayed": result.replayed,
                        "organization_id": row.organization_id,
                        "audience_scope": {
                            "session_id": row.audience.session_id,
                            "group_ids": row.audience.group_ids,
                        },
                        "learning_objective_refs": tuple(
                            r.material() for r in row.source.objective_refs
                        ),
                        "source_activity_ref": {
                            "activity_id": row.source.source_ref.ref,
                            "version": row.source.source_ref.version,
                            "hash": row.source.source_ref.hash,
                        },
                        "effective_activity_snapshot": {
                            "definition_ref": row.source.definition_ref.material(),
                            "title": snapshot.title,
                            "instructions": snapshot.instructions,
                            "materials": snapshot.materials,
                            "safety": snapshot.safety,
                            "duration_note": snapshot.duration_note,
                            "form": snapshot.form,
                            "observation_prompts": snapshot.observation_prompts,
                        },
                        "state": row.state.value,
                        "selected_by": row.selected_by,
                        "created_at": row.created_at,
                        "started_at": row.started_at,
                        "finished_at": row.finished_at,
                        "invalidation_reason": row.invalidated,
                        "outcome_delivery": result.outcome_delivery,
                    },
                    strict=True,
                )
            except (ValueError, TypeError, AttributeError):
                raise RuntimeError("invalid service projection") from None
            return JSONResponse(
                {"correlation_id": correlation, "data": view.model_dump(mode="json")},
                status_code=200,
                headers={"Cache-Control": "no-store", "Vary": "Authorization"},
            )
        except _InputError as exc:
            return _error(correlation, exc.status, exc.code.replace("VIDEO_REVIEW_", "ACTIVITY_"))
        except VideoError as exc:
            code = str(exc) if str(exc) in _CODES else "ACTIVITY_DEPENDENCY_UNAVAILABLE"
            if str(exc) in {
                "ACTIVITY_INVALID_TEXT",
                "ACTIVITY_INVALID_IDS",
                "ACTIVITY_INVALID_COMMAND",
                "ACTIVITY_REASON_REQUIRED",
                "ACTIVITY_INVALID_ADAPTATION",
            }:
                return _error(correlation, 422, "ACTIVITY_INVALID_COMMAND")
            return _error(correlation, _CODES[code], code)
        except Exception:
            return _error(correlation, 503, "ACTIVITY_DEPENDENCY_UNAVAILABLE")

    return router
