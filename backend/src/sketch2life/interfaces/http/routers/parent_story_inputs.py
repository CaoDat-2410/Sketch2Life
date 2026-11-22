"""Parent StoryRun input routes: drawing (T-2b), idea and transcript (T-2c); SRS l.1664-1665.

Same literal prefix as ``parent_story_runs`` (``/v1/story-runs``), in its own module so T-2c (idea,
audio, transcript) and T-2d (story rewrite) add routes here without editing the lifecycle router.
T-2c routes: ``POST /{run_id}/idea``, ``GET /{run_id}/transcript`` and
``POST /{run_id}/transcript-confirmation`` (TD-04). The router
is mounted and unmounted together with ``parent_story_runs`` while the StoryRun-lite demo is on or
off (``story_demo_replaced_routers`` records it): the demo owns
``POST /v1/story-runs/{run_ref}/assets`` with another contract.
"""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAttachOutcome,
    IdeaOutcome,
    TranscriptConfirmOutcome,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    StoryRewriteOutcome,
)
from sketch2life.application.ports.story_run_actor import RunActor
from sketch2life.contracts.schemas.parent_story_inputs import (
    AddRunIdeaRequestV1,
    AttachRunAssetRequestV1,
    ConfirmTranscriptRequestV1,
    IdeaTranscriptRefV1,
    ParentRunAssetAcceptedV1,
    ParentRunIdeaAcceptedV1,
    ParentRunTranscriptV1,
    ParentStoryRewriteAcceptedV1,
    ParentTranscriptConfirmationV1,
    RewriteStoryRequestV1,
)
from sketch2life.contracts.schemas.parent_story_runs import (
    ParentStoryErrorEnvelopeV1,
    ParentStoryRunLifecycleEnvelopeV1,
)
from sketch2life.infrastructure.story_inputs.idea import ParentRunIdeaService
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_inputs.service import ParentRunAssetService
from sketch2life.infrastructure.story_inputs.speech import ParentSpeechJobRunner
from sketch2life.infrastructure.story_inputs.story_generation import (
    REWRITE_NEUTRAL_INSTRUCTION_V1,
    REWRITE_NEUTRAL_INSTRUCTION_VERSION,
    STORY_REWRITE_MODEL_ID,
    STORY_REWRITE_MODEL_REVISION,
    STORY_REWRITE_PROMPT_VERSION,
    ParentStoryRewriteRunner,
)
from sketch2life.interfaces.http.api_conventions import parse_idempotency_key
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.story_run_actor import (
    require_story_run_actor,
    story_run_repository,
)

router = APIRouter(prefix="/v1/story-runs", tags=["Parent StoryRuns"])

_ASSET_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run or asset was not found, or the caller is neither the active Parent owner nor "
            "the Teacher currently responsible for the run."
        ),
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The run state or revision does not allow this drawing.",
    },
    413: {"model": ParentStoryErrorEnvelopeV1, "description": "The image is too large."},
    415: {"model": ParentStoryErrorEnvelopeV1, "description": "The asset is not a drawing image."},
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The image failed validation (dimensions, content, checksum).",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}


def _job_actor(actor: RunActor, organization_id: str | None = None) -> tuple[Any, ...]:
    """The extra runner arguments of a Teacher run (T-4b3a D6); none for a Parent, so the Parent
    background task is called exactly as before."""

    if not actor.is_teacher:
        return ()
    return (actor, organization_id) if organization_id is not None else (actor,)


def _http_error(exc: ParentStoryRunError) -> HTTPException:
    """The story envelope detail: the code, ``current_version`` and plain ``field_errors``."""
    detail: dict[str, Any] = {"code": exc.code}
    if exc.current_version is not None:
        detail["current_version"] = exc.current_version
    if exc.field_errors:
        detail["field_errors"] = exc.field_errors
    return HTTPException(status_code=exc.status_code, detail=detail)


@router.post(
    "/{run_id}/assets",
    response_model=ParentRunAssetAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Attach a completed artwork upload to the Parent StoryRun as its drawing",
    responses=_ASSET_ERROR_RESPONSES,
)
def attach_parent_run_asset(
    run_id: UUID,
    payload: AttachRunAssetRequestV1,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentRunAssetAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1:
    # The declaration above publishes the header as required; parse_idempotency_key (1-128
    # visible ASCII) is the authority and runs after the role check, before the run lookup.
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    state = request.app.state
    service = ParentRunAssetService(
        db,
        storage=getattr(state, "lesson_library_storage", None),
        repository=story_run_repository(db, actor),
    )
    try:
        result = service.attach_drawing(
            principal=principal,
            run_id=str(run_id),
            asset_ref=payload.asset_ref,
            expected_run_revision=payload.expected_run_revision,
            idempotency_key=key,
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if isinstance(result, ParentStoryLifecycleRecord):
        return ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": result.as_body()}
        )
    analyzer = getattr(state, "drawing_analyzer", None)
    runtime = getattr(state, "be1_runtime", None)
    if (
        analyzer is not None
        and runtime is not None
        and runtime.session_factory is not None
        and not result.replayed
    ):
        runner = ParentInputJobRunner(runtime.session_factory, analyzer)
        background_tasks.add_task(
            runner.run,
            principal,
            str(run_id),
            result.input_revision,
            *_job_actor(actor, result.organization_id),
        )
    return _accepted(run_id, payload.asset_ref, result)


def _accepted(
    run_id: UUID, asset_ref: str, outcome: DrawingAttachOutcome
) -> ParentRunAssetAcceptedV1:
    return ParentRunAssetAcceptedV1.model_validate(
        {
            "request_id": uuid4(),
            "story_run_id": run_id,
            "asset_ref": asset_ref,
            "asset_kind": "DRAWING",
            "asset_state": "READY",
            "input_revision": outcome.input_revision,
            "run_revision": outcome.run_revision,
            "run_state": outcome.run_state,
            "analysis_state": outcome.analysis_state,
        }
    )


_IDEA_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run or the audio was not found, or the caller is neither the active Parent owner "
            "nor the Teacher currently responsible for the run."
        ),
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The run state or a revision does not allow this command.",
    },
    413: {"model": ParentStoryErrorEnvelopeV1, "description": "The audio is too large or long."},
    415: {"model": ParentStoryErrorEnvelopeV1, "description": "The asset is not accepted audio."},
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The audio failed validation (content, checksum, completeness).",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}
_TRANSCRIPT_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run was not found, or the caller is neither the active Parent owner nor the "
            "Teacher currently responsible for the run."
        ),
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "The run state or the transcript revision does not allow this.",
    },
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "Validation uses the standard error envelope.",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}


@router.post(
    "/{run_id}/idea",
    response_model=ParentRunIdeaAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Add the adult's idea (text and/or audio) or correct the transcript of a Parent run",
    responses=_IDEA_ERROR_RESPONSES,
)
def add_parent_run_idea(
    run_id: UUID,
    payload: AddRunIdeaRequestV1,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentRunIdeaAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1:
    # See attach_parent_run_asset: parse_idempotency_key is the authority and runs after the role
    # check, before the run lookup.
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    state = request.app.state
    service = ParentRunIdeaService(
        db,
        storage=getattr(state, "lesson_library_storage", None),
        repository=story_run_repository(db, actor),
    )
    try:
        result = service.submit(
            principal=principal, run_id=str(run_id), payload=payload, idempotency_key=key
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if isinstance(result, ParentStoryLifecycleRecord):
        return ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": result.as_body()}
        )
    transcriber = getattr(state, "speech_transcriber", None)
    runtime = getattr(state, "be1_runtime", None)
    if (
        transcriber is not None
        and runtime is not None
        and runtime.session_factory is not None
        and result.new_transcript_id is not None
        and not result.replayed
    ):
        speech = ParentSpeechJobRunner(runtime.session_factory, transcriber)
        background_tasks.add_task(
            speech.run,
            principal,
            str(run_id),
            result.new_transcript_id,
            *_job_actor(actor, result.organization_id),
        )
    return _idea_accepted(run_id, result)


def _idea_accepted(run_id: UUID, outcome: IdeaOutcome) -> ParentRunIdeaAcceptedV1:
    transcript = (
        None
        if outcome.transcript_revision is None or outcome.transcript_state is None
        else IdeaTranscriptRefV1.model_validate(
            {
                "transcript_revision": outcome.transcript_revision,
                "state": outcome.transcript_state,
            }
        )
    )
    return ParentRunIdeaAcceptedV1.model_validate(
        {
            "request_id": uuid4(),
            "story_run_id": run_id,
            "input_revision": outcome.input_revision,
            "run_revision": outcome.run_revision,
            "run_state": outcome.run_state,
            "idea_source": outcome.idea_source,
            "transcript": transcript,
        }
    )


@router.get(
    "/{run_id}/transcript",
    response_model=ParentRunTranscriptV1,
    summary="Read the current transcript of the Parent run's voice idea",
    responses=_TRANSCRIPT_ERROR_RESPONSES,
)
def get_parent_run_transcript(
    run_id: UUID,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentRunTranscriptV1:
    actor = require_story_run_actor(db, principal)
    try:
        view = story_run_repository(db, actor).get_transcript(
            principal=principal, run_id=str(run_id)
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    # The transcript is a child's words: never cached, never logged (l.942, NFR-03).
    response.headers["Cache-Control"] = "private, no-store"
    return ParentRunTranscriptV1.model_validate(
        {
            "story_run_id": run_id,
            "transcript_revision": view.transcript_revision,
            "state": view.state,
            "origin": view.origin,
            "text": view.text,
            "transcript_sha256": view.transcript_sha256,
            "language": view.language,
            "error_code": view.error_code,
            "run_revision": view.run_revision,
        }
    )


@router.post(
    "/{run_id}/transcript-confirmation",
    response_model=ParentTranscriptConfirmationV1 | ParentStoryRunLifecycleEnvelopeV1,
    summary="Confirm one exact transcript revision of the Parent run's voice idea",
    responses=_TRANSCRIPT_ERROR_RESPONSES,
)
def confirm_parent_run_transcript(
    run_id: UUID,
    payload: ConfirmTranscriptRequestV1,
    request: Request,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentTranscriptConfirmationV1 | ParentStoryRunLifecycleEnvelopeV1:
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    try:
        result = story_run_repository(db, actor).confirm_transcript(
            principal=principal,
            run_id=str(run_id),
            idempotency_key=key,
            expected_transcript_revision=payload.expected_transcript_revision,
            transcript_sha256=payload.transcript_sha256,
        )
    except ParentStoryRunError as exc:
        raise _http_error(exc) from None
    response.headers["Cache-Control"] = "private, no-store"
    if isinstance(result, ParentStoryLifecycleRecord):
        return ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": result.as_body()}
        )
    return _transcript_confirmed(run_id, result)


def _transcript_confirmed(
    run_id: UUID, outcome: TranscriptConfirmOutcome
) -> ParentTranscriptConfirmationV1:
    return ParentTranscriptConfirmationV1.model_validate(
        {
            "request_id": uuid4(),
            "story_run_id": run_id,
            "transcript_revision": outcome.transcript_revision,
            "state": "CONFIRMED",
            "run_revision": outcome.run_revision,
            "run_state": outcome.run_state,
        }
    )


_REWRITE_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ParentStoryErrorEnvelopeV1, "description": "The request is invalid."},
    401: {"model": ParentStoryErrorEnvelopeV1, "description": "Authentication is required."},
    404: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run was not found, or the caller is neither the active Parent owner nor the "
            "Teacher currently responsible for the run."
        ),
    },
    409: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": (
            "The run state does not allow a rewrite, the story revision is stale, or the "
            "rewrite limit is reached."
        ),
    },
    422: {
        "model": ParentStoryErrorEnvelopeV1,
        "description": "A precondition of the story is not met (subject, context or transcript).",
    },
    503: {"model": ParentStoryErrorEnvelopeV1, "description": "A required service is unavailable."},
    500: {"model": ParentStoryErrorEnvelopeV1, "description": "An unexpected error occurred."},
}
# Repository codes of the legacy story route that the SRS route reports with a published code.
_REWRITE_CODE_MAP = {
    "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT": "INVALID_STATE_TRANSITION",
    "PARENT_STORY_REWRITE_NOT_ALLOWED": "INVALID_STATE_TRANSITION",
    "PARENT_UNDERSTANDING_REVISION_STALE": "INVALID_STATE_TRANSITION",
    "PARENT_STORY_ARTWORK_REQUIRED": "INVALID_STATE_TRANSITION",
    "PARENT_VISIBLE_FEATURES_UNAVAILABLE": "INVALID_STATE_TRANSITION",
}


@router.post(
    "/{run_id}/story-rewrites",
    response_model=ParentStoryRewriteAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ask for one more revision of the Parent run's story (at most three rewrites)",
    responses=_REWRITE_ERROR_RESPONSES,
)
def rewrite_parent_run_story(
    run_id: UUID,
    payload: RewriteStoryRequestV1,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)],
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> ParentStoryRewriteAcceptedV1 | ParentStoryRunLifecycleEnvelopeV1:
    """SRS l.1668, FR-P-07: 202 with the new revision number; 409 at the limit or when stale.

    The adult's hint is untrusted data in its own worker field; with no hint the server sends the
    constant neutral instruction. The generation runs after the response when a story generator
    is composed; otherwise the run waits in ``SCRIPT_GENERATING`` and can be cancelled.
    """
    del idempotency_key
    actor = require_story_run_actor(db, principal)
    key = parse_idempotency_key(request)
    state = request.app.state
    try:
        outcome = story_run_repository(db, actor).reserve_story_rewrite(
            principal=principal,
            run_id=str(run_id),
            idempotency_key=key,
            expected_story_revision=payload.expected_story_revision,
            expected_story_sha256=payload.expected_story_sha256,
            hint=payload.hint,
            story_revision_id=str(uuid4()),
            model_id=STORY_REWRITE_MODEL_ID,
            model_revision=STORY_REWRITE_MODEL_REVISION,
            prompt_version=STORY_REWRITE_PROMPT_VERSION,
            instruction_version=REWRITE_NEUTRAL_INSTRUCTION_VERSION,
            instruction=REWRITE_NEUTRAL_INSTRUCTION_V1,
        )
    except ParentStoryRunError as exc:
        mapped = _REWRITE_CODE_MAP.get(exc.code)
        if mapped is not None:
            exc = ParentStoryRunError(exc.status_code, mapped, current_version=exc.current_version)
        raise _http_error(exc) from None
    response.headers["Content-Location"] = f"/v1/story-runs/{run_id}"
    if outcome.lifecycle is not None:
        return ParentStoryRunLifecycleEnvelopeV1.model_validate(
            {"request_id": uuid4(), "lifecycle": outcome.lifecycle.as_body()}
        )
    generator = getattr(state, "story_generator", None)
    runtime = getattr(state, "be1_runtime", None)
    if (
        generator is not None
        and runtime is not None
        and runtime.session_factory is not None
        and outcome.reservation is not None
        and not outcome.replayed
    ):
        runner = ParentStoryRewriteRunner(runtime.session_factory, generator)
        background_tasks.add_task(runner.run, principal, outcome.reservation, *_job_actor(actor))
    return _rewrite_accepted(run_id, outcome)


def _rewrite_accepted(run_id: UUID, outcome: StoryRewriteOutcome) -> ParentStoryRewriteAcceptedV1:
    return ParentStoryRewriteAcceptedV1.model_validate(
        {
            "request_id": uuid4(),
            "story_run_id": run_id,
            "story_revision_no": outcome.story_revision_no,
            "run_revision": outcome.run_revision,
            "run_state": outcome.run_state,
        }
    )


__all__ = ["router"]
