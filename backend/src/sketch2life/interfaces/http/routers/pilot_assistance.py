"""Local/test synthetic assistance gateway over the existing BE1 auth boundary."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from collections.abc import AsyncIterator
from contextvars import ContextVar, Token
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Connection
from sqlalchemy.orm import Session

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.ports.assistance import (
    AnalysisOutcome,
    AnalysisOutcomePort,
    AssistanceAuthority,
    AssistanceAuthorityPort,
    AssistanceJobPort,
    AssistanceJobReader,
    AssistancePolicyPort,
    AssistanceSourcePort,
    CanvasFacts,
    SketchIntent,
    SketchStagePort,
)
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.ai_jobs import AiJobService
from sketch2life.application.services.assistance import (
    AssistanceDependencies,
    AssistanceError,
    AssistanceService,
    CancelCommand,
    CommandResult,
    SubmitCommand,
)
from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1
from sketch2life.domain.ai_jobs.model import JobState, ResultDisposition
from sketch2life.domain.assistance import (
    AssistanceRequest,
    Contributor,
    PolicySnapshot,
    RequestStatus,
    TargetKind,
)
from sketch2life.domain.vision_analysis import VISION_ANALYSIS_JOB_TYPE
from sketch2life.infrastructure.assistance.adapters import (
    AiJobRepositoryReader,
    AiJobServicePort,
)
from sketch2life.infrastructure.assistance.be1_canvas_source_adapter import (
    PostgresCanvasSourceAdapter,
)
from sketch2life.infrastructure.assistance.be1_owner_adapter import (
    PostgresAssistanceOwnerAdapter,
)
from sketch2life.infrastructure.assistance.pilot_policy import (
    PilotSyntheticPolicy,
)
from sketch2life.infrastructure.assistance.sql_repository import SqlAssistanceRepository
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.be1_runtime import (
    Be1Runtime,
    VerifiedDeviceContext,
    VerifiedDeviceStatusContext,
    get_db,
    get_runtime,
    get_verified_adult,
    get_verified_device,
    get_verified_device_status,
)
from sketch2life.interfaces.http.routers.assistance_requests import (
    build_assistance_requests_router,
)
from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export
from sketch2life.interfaces.http.routers.be1_common import get_session, require_assignment

_CURRENT_CANDIDATE_REQUEST: ContextVar[Request | None] = ContextVar(
    "pilot_assistance_candidate_request", default=None
)
_POLL_AFTER_MS = 2000
_PENDING_REQUEST_STATES = frozenset(
    {RequestStatus.SCHEDULING, RequestStatus.SCHEDULED, RequestStatus.ANALYSIS_READY}
)


class ChildAssistanceStatusV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assistance_id: str
    request_revision: int
    status: Literal["pending", "cancelled", "unavailable"]
    processing_state: Literal["processing", "submitted_to_teacher", "unknown"]
    poll_after_ms: int | None


class TeacherPendingItemV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    assistance_id: str
    request_revision: int
    session_id: str
    canvas_id: str
    participant_id: str
    requested_level: str
    request_reason: str
    status: str
    processing_state: Literal["processing", "submitted_to_teacher", "unknown"]
    created_at: datetime


class TeacherPendingListV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    items: tuple[TeacherPendingItemV1, ...]


@dataclass(frozen=True, slots=True)
class _ChildAssistanceBinding:
    owner: PostgresAssistanceOwnerAdapter
    service: AssistanceService


class _NoAnalysisOutcomes(AnalysisOutcomePort):
    """T9 reads job lineage only; analysis rows are intentionally outside this boundary."""

    def for_attempt(
        self, organization_id: str, job_id: str, attempt_id: str
    ) -> AnalysisOutcome | None:
        del organization_id, job_id, attempt_id
        return None

    def current(self, organization_id: str, analysis_id: str) -> AnalysisOutcome | None:
        del organization_id, analysis_id
        return None


class _NoSketchStage(SketchStagePort):
    def request_sketch(self, intent: SketchIntent) -> None:
        del intent


class _NoCachePilotPolicy(AssistancePolicyPort):
    def __init__(self, settings: Settings) -> None:
        self._pilot = PilotSyntheticPolicy(
            environment=settings.env,
            pilot_enabled=settings.synthetic_pilot_enabled is True,
        )

    def current(
        self, organization_id: str, session_id: str
    ) -> PolicySnapshot | None:
        current = self._pilot.current(organization_id, session_id)
        return None if current is None else replace(current, cache_enabled=False)


class _ChildAssistanceAuthority(AssistanceAuthorityPort):
    def __init__(self, context: VerifiedDeviceContext) -> None:
        self._context = context

    def decide(self, principal: Principal, canvas: CanvasFacts) -> AssistanceAuthority:
        context = self._context
        if (
            principal.role is not PrincipalRole.DEVICE
            or principal.principal_id != context.principal.principal_id
            or principal.organization_id != context.session.organization_id
            or canvas.organization_id != context.session.organization_id
            or canvas.session_id != context.session.session_id
            or canvas.canvas_id != context.turn.canvas_id
            or canvas.group_id != context.membership.group_id
        ):
            return AssistanceAuthority(False)
        return AssistanceAuthority(
            True,
            contributor=Contributor(
                context.membership.child_id,
                context.turn.turn_id,
                context.turn.revision,
            ),
        )

    def disclose(self, principal: Principal, request: AssistanceRequest) -> bool:
        context = self._context
        target = request.facts.target
        return (
            principal.role is PrincipalRole.DEVICE
            and principal.principal_id == context.principal.principal_id
            and principal.organization_id == request.facts.organization_id
            and request.facts.organization_id == context.session.organization_id
            and request.facts.session_id == context.session.session_id
            and request.facts.canvas_id == context.turn.canvas_id
            and request.requester.principal_id == context.principal.principal_id
            and target.kind is TargetKind.INDIVIDUAL
            and target.ref_id == context.membership.child_id
        )


class _RequestBoundAssistanceService:
    """Adapt the candidate router to one authenticated device request at a time."""

    @property
    def poll_after_ms(self) -> int:
        return _POLL_AFTER_MS

    def submit(self, command: SubmitCommand) -> CommandResult:
        request = _CURRENT_CANDIDATE_REQUEST.get()
        if request is None:
            raise AssistanceError("DEPENDENCY_UNAVAILABLE")
        context = cast(VerifiedDeviceContext, request.state.pilot_device_context)
        runtime = cast(Be1Runtime, request.state.pilot_runtime)
        if runtime.engine is None:
            raise AssistanceError("DEPENDENCY_UNAVAILABLE")
        with runtime.engine.connect() as connection:
            binding = _build_child_binding(runtime, context, connection)
            canvas = binding.owner.canvas(command.principal.organization_id, command.canvas_id)
            if canvas is None:
                raise AssistanceError("RESOURCE_NOT_FOUND")
            server_owned = replace(command, context_revision=canvas.context_revision)
            return binding.service.submit(server_owned)

    def cancel(self, command: CancelCommand) -> CommandResult:
        request = _CURRENT_CANDIDATE_REQUEST.get()
        if request is None:
            raise AssistanceError("DEPENDENCY_UNAVAILABLE")
        context = cast(VerifiedDeviceContext, request.state.pilot_device_context)
        runtime = cast(Be1Runtime, request.state.pilot_runtime)
        if runtime.engine is None:
            raise AssistanceError("DEPENDENCY_UNAVAILABLE")
        with runtime.engine.connect() as connection:
            binding = _build_child_binding(runtime, context, connection)
            return binding.service.cancel(command)


def _build_child_binding(
    runtime: Be1Runtime,
    context: VerifiedDeviceContext,
    connection: Connection,
) -> _ChildAssistanceBinding:
    if runtime.engine is None or runtime.pilot_job_repository is None:
        raise AssistanceError("DEPENDENCY_UNAVAILABLE")
    vision = runtime.pilot_vision
    jobs = getattr(vision, "jobs", None)
    if not isinstance(jobs, AiJobService):
        raise AssistanceError("DEPENDENCY_UNAVAILABLE")

    def export_source(
        organization_id: str, canvas_id: str
    ) -> CanvasSourceExportV1:
        """Export only the verified active device's current canvas epoch."""
        with Session(bind=connection) as session:
            return build_canvas_source_export(
                session,
                organization_id=organization_id,
                session_id=context.session.session_id,
                canvas_id=canvas_id,
                document_epoch=context.turn.document_epoch,
            )

    owner = PostgresAssistanceOwnerAdapter(
        connection,
        organization_id=context.session.organization_id,
        class_id=context.session.class_id,
        session_id=context.session.session_id,
        environment=runtime.settings.env,
        pilot_enabled=runtime.settings.synthetic_pilot_enabled is True,
        export_source=export_source,
    )
    sources = PostgresCanvasSourceAdapter(
        connection,
        session_id=context.session.session_id,
        export_source=export_source,
        load_artifact=runtime.artifact_store.get,
        environment=runtime.settings.env,
        pilot_enabled=runtime.settings.synthetic_pilot_enabled is True,
    )
    service = AssistanceService(
        AssistanceDependencies(
            repository=SqlAssistanceRepository(runtime.engine, context.session.organization_id),
            owner=owner,
            authority=_ChildAssistanceAuthority(context),
            sources=cast(AssistanceSourcePort, sources),
            policy=_NoCachePilotPolicy(runtime.settings),
            jobs=cast(AssistanceJobPort, AiJobServicePort(jobs)),
            job_reader=cast(
                AssistanceJobReader,
                AiJobRepositoryReader(runtime.pilot_job_repository),
            ),
            analyses=_NoAnalysisOutcomes(),
            sketch_stage=_NoSketchStage(),
            clock=_UtcClock(),
            ids=_UuidIds(),
            auto_schedule=True,
            analysis_only=True,
        )
    )
    return _ChildAssistanceBinding(owner, service)


class _UtcClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class _UuidIds:
    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"


def _require_pilot_runtime(runtime: Be1Runtime = Depends(get_runtime)) -> Be1Runtime:
    if (
        runtime.settings.env not in {"local", "test"}
        or runtime.settings.synthetic_pilot_enabled is not True
        or runtime.pilot_vision is None
    ):
        raise HTTPException(
            status_code=503,
            detail={"code": "PILOT_ASSISTANCE_DISABLED"},
            headers={"Cache-Control": "no-store"},
        )
    return runtime


async def _bind_child_request(
    request: Request,
    runtime: Be1Runtime = Depends(_require_pilot_runtime),
    context: VerifiedDeviceContext = Depends(get_verified_device),
) -> AsyncIterator[None]:
    request.state.pilot_runtime = runtime
    request.state.pilot_device_context = context
    token: Token[Request | None] = _CURRENT_CANDIDATE_REQUEST.set(request)
    try:
        yield
    finally:
        _CURRENT_CANDIDATE_REQUEST.reset(token)


def _resolve_child_principal(request: Request) -> Principal | None:
    context = getattr(request.state, "pilot_device_context", None)
    if not isinstance(context, VerifiedDeviceContext):
        return None
    return Principal(
        context.principal.principal_id,
        context.session.organization_id,
        PrincipalRole.DEVICE,
    )


def _read_request(
    runtime: Be1Runtime, organization_id: str, assistance_id: str
) -> AssistanceRequest | None:
    if runtime.engine is None:
        raise HTTPException(status_code=503, detail={"code": "PILOT_LEDGER_UNAVAILABLE"})
    try:
        with SqlAssistanceRepository(runtime.engine, organization_id).transaction() as tx:
            return tx.get(assistance_id)
    except Exception:
        raise HTTPException(
            status_code=503, detail={"code": "PILOT_LEDGER_UNAVAILABLE"}
        ) from None


def _read_requests(runtime: Be1Runtime, organization_id: str) -> tuple[AssistanceRequest, ...]:
    if runtime.engine is None:
        raise HTTPException(status_code=503, detail={"code": "PILOT_LEDGER_UNAVAILABLE"})
    try:
        with SqlAssistanceRepository(runtime.engine, organization_id).transaction() as tx:
            return tx.list_requests(organization_id)
    except Exception:
        raise HTTPException(
            status_code=503, detail={"code": "PILOT_LEDGER_UNAVAILABLE"}
        ) from None


def _job_processing_state(
    runtime: Be1Runtime,
    *,
    organization_id: str,
    request: AssistanceRequest,
) -> Literal["processing", "submitted_to_teacher", "unknown"]:
    repository = runtime.pilot_job_repository
    job_id = request.job_id
    if repository is None or job_id is None:
        return "unknown"
    try:
        with repository.transaction() as tx:
            job = tx.get_job(job_id)
            if job is None:
                return "unknown"
            ref = job.active_attempt.request_ref
            if (
                job.organization_id != organization_id
                or job.job_type != VISION_ANALYSIS_JOB_TYPE
                or job.scope.session_id != request.facts.session_id
                or job.scope.target_id != request.assistance_id
                or ref.request_id != request.assistance_id
                or ref.request_revision != request.request_revision
            ):
                return "unknown"
            receipt = tx.get_completion_receipt(job.job_id, job.active_attempt.attempt_id)
    except Exception:
        return "unknown"

    accepted = (
        job.state is JobState.SUCCEEDED
        and job.result_disposition is ResultDisposition.ACCEPTED
        and bool(job.result_refs)
        and job.completed_at is not None
        and job.active_attempt.outcome == "succeeded:accepted"
        and receipt is not None
        and receipt.authoritative
        and receipt.job_id == job.job_id
        and receipt.attempt_id == job.active_attempt.attempt_id
        and receipt.disposition is ResultDisposition.ACCEPTED
        and receipt.job_revision_after == job.job_revision
    )
    if accepted:
        return "submitted_to_teacher"
    if job.state in {
        JobState.QUEUED,
        JobState.RUNNING,
        JobState.FAILED_RETRYABLE,
    }:
        return "processing"
    return "unknown"


def _device_status(request: AssistanceRequest) -> Literal["pending", "cancelled", "unavailable"]:
    if request.status is RequestStatus.CANCELLED:
        return "cancelled"
    if request.status in _PENDING_REQUEST_STATES:
        return "pending"
    return "unavailable"


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "ASSISTANCE_REQUEST_NOT_FOUND"})


router = APIRouter(tags=["pilot-assistance"])
router.include_router(
    build_assistance_requests_router(
        cast(AssistanceService, _RequestBoundAssistanceService()),
        _resolve_child_principal,
        prefix="/api/be1/v1",
    ),
    dependencies=[Depends(_bind_child_request)],
)


@router.get(
    "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status",
    response_model=ChildAssistanceStatusV1,
    summary="Read the requesting child's assistance status",
    description=(
        "Returns only the admitted child's own coarse processing state. Model output and "
        "analysis records are never included."
    ),
)
def child_status(
    organization_id: str,
    session_id: str,
    assistance_id: str,
    runtime: Be1Runtime = Depends(_require_pilot_runtime),
    context: VerifiedDeviceStatusContext = Depends(get_verified_device_status),
) -> JSONResponse:
    if (
        context.grant.organization_id != organization_id
        or context.grant.session_id != session_id
    ):
        raise _not_found()
    request = _read_request(runtime, organization_id, assistance_id)
    if request is None:
        raise _not_found()
    child_id = context.membership.child_id
    if (
        request.facts.organization_id != organization_id
        or request.facts.session_id != session_id
        or request.facts.group_id != context.membership.group_id
        or request.facts.canvas_id != context.membership.group_id
        or request.facts.target.kind is not TargetKind.INDIVIDUAL
        or request.facts.target.ref_id != child_id
        or request.requester.principal_id != f"device:{context.grant.grant_id}"
    ):
        raise _not_found()
    processing = _job_processing_state(
        runtime, organization_id=organization_id, request=request
    )
    status = _device_status(request)
    return JSONResponse(
        ChildAssistanceStatusV1(
            assistance_id=request.assistance_id,
            request_revision=request.request_revision,
            status=status,
            processing_state=processing,
            poll_after_ms=_POLL_AFTER_MS if status == "pending" else None,
        ).model_dump(mode="json"),
        headers={"Cache-Control": "no-store", "Vary": "Authorization"},
    )


@router.get(
    "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending",
    response_model=TeacherPendingListV1,
    summary="List assigned teacher's pending assistance metadata",
    description=(
        "Lists pending request metadata for an assigned Teacher while the session is active "
        "or paused. This operation does not approve or reject a request."
    ),
)
def teacher_pending(
    organization_id: str,
    session_id: str,
    runtime: Be1Runtime = Depends(_require_pilot_runtime),
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    db: Session = Depends(get_db),
) -> JSONResponse:
    session = get_session(db, organization_id, session_id)
    if session.state not in {"active", "paused"}:
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND"})
    require_assignment(
        db,
        principal,
        organization_id,
        roles={"school_admin", "teacher"},
        class_id=session.class_id,
    )
    items = []
    for request in _read_requests(runtime, organization_id):
        if (
            request.facts.session_id != session_id
            or request.status not in _PENDING_REQUEST_STATES
            or request.facts.target.kind is not TargetKind.INDIVIDUAL
        ):
            continue
        items.append(
            TeacherPendingItemV1(
                assistance_id=request.assistance_id,
                request_revision=request.request_revision,
                session_id=session_id,
                canvas_id=request.facts.canvas_id,
                participant_id=request.facts.target.ref_id,
                requested_level=request.requested_level,
                request_reason=str(request.request_reason),
                status=str(request.status),
                processing_state=_job_processing_state(
                    runtime, organization_id=organization_id, request=request
                ),
                created_at=request.created_at,
            )
        )
    response = TeacherPendingListV1(items=tuple(items))
    return JSONResponse(
        response.model_dump(mode="json"),
        headers={"Cache-Control": "no-store", "Vary": "Authorization"},
    )


__all__ = [
    "ChildAssistanceStatusV1",
    "TeacherPendingListV1",
    "router",
]
