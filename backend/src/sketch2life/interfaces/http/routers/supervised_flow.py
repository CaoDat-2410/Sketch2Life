"""Explicit adult review, deterministic P1, P4 fallback, handoff, and feedback routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from sketch2life.application.services.auto_rig import AutoRigPackageUnavailable, AutoRigService
from sketch2life.application.services.ephemeral_sessions import (
    SessionWorkflowError,
    failure_result,
)
from sketch2life.application.services.supervised_flow import SupervisedFlowService
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
)

router = APIRouter(prefix="/v1/sessions", tags=["supervised-flow"])
renderer_source_router = APIRouter(tags=["renderer"])


@router.post("/{session_id}/media/retake", response_model=MobileWorkflowResultV1)
def request_retake(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("request_retake", session_id, command, request)


@router.post("/{session_id}/gate-a/confirm", response_model=MobileWorkflowResultV1)
def confirm_gate_a(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("confirm_gate_a", session_id, command, request)


@router.put("/{session_id}/p1-context", response_model=MobileWorkflowResultV1)
def set_p1_context(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("set_p1_context", session_id, command, request)


@router.post("/{session_id}/p1-filter", response_model=MobileWorkflowResultV1)
def run_p1_filter(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("run_p1_filter", session_id, command, request)


@router.post("/{session_id}/experience/prepare", response_model=MobileWorkflowResultV1)
def prepare_experience(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("prepare_experience", session_id, command, request)


@router.post("/{session_id}/gate-b/approve", response_model=MobileWorkflowResultV1)
def approve_gate_b(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("approve_gate_b", session_id, command, request)


@router.post("/{session_id}/handoff", response_model=MobileWorkflowResultV1)
def complete_handoff(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("complete_handoff", session_id, command, request)


@router.post("/{session_id}/renderer/launch", response_model=MobileWorkflowResultV1)
def prepare_renderer(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("prepare_renderer", session_id, command, request)


@router.post("/{session_id}/feedback", response_model=MobileWorkflowResultV1)
def record_feedback(
    session_id: str, command: MobileWorkflowCommandV1, request: Request
) -> JSONResponse:
    return _execute("record_feedback", session_id, command, request)


@router.get("/{session_id}/p1/context-options", response_model=MobileWorkflowResultV1)
def read_p1_context_options(
    session_id: str,
    request: Request,
    request_id: Annotated[str, Header(alias="X-Request-ID", min_length=1, max_length=120)],
    expected_session_version: Annotated[int, Header(alias="X-Expected-Session-Version", ge=0)],
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
    age_months: Annotated[int, Query(alias="age_months", ge=0, le=155)],
) -> JSONResponse:
    service: SupervisedFlowService | None = request.app.state.supervised_flow_service
    if service is None:
        error = SessionWorkflowError(
            code="SUPERVISED_FLOW_NOT_CONFIGURED",
            status_code=503,
            safe_message="The supervised demo flow is not configured.",
        )
        return _failure(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    try:
        result = service.read_p1_context_options(
            session_id=session_id,
            request_id=request_id,
            expected_version=expected_session_version,
            actor_ref=actor_ref,
            age_months=age_months,
        )
    except SessionWorkflowError as error:
        return _failure(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


@router.get("/{session_id}/gallery", response_model=MobileWorkflowResultV1)
def read_gallery(
    session_id: str,
    request: Request,
    request_id: Annotated[str, Header(alias="X-Request-ID", min_length=1, max_length=120)],
    expected_session_version: Annotated[int, Header(alias="X-Expected-Session-Version", ge=0)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
) -> JSONResponse:
    del idempotency_key
    service: SupervisedFlowService | None = request.app.state.supervised_flow_service
    if service is None:
        error = SessionWorkflowError(
            code="SUPERVISED_FLOW_NOT_CONFIGURED",
            status_code=503,
            safe_message="The supervised demo flow is not configured.",
        )
        return _failure(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    try:
        result = service.read_gallery(
            session_id=session_id,
            request_id=request_id,
            expected_version=expected_session_version,
            actor_ref=actor_ref,
        )
    except SessionWorkflowError as error:
        return _failure(
            error,
            request_id=request_id,
            session_id=session_id,
            expected_version=expected_session_version,
        )
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


@renderer_source_router.get("/v1/renderer/source")
def read_renderer_source(
    request: Request,
    capability: Annotated[
        str,
        Header(alias="X-Render-Source-Capability", min_length=40, max_length=200),
    ],
) -> Response:
    service = request.app.state.live_image_demo_service
    if service is None:
        return JSONResponse(status_code=503, content={"code": "RENDERER_NOT_CONFIGURED"})
    try:
        content_type, body = service.read_renderer_source(capability)
    except SessionWorkflowError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"code": error.code, "message": error.safe_message},
        )
    return Response(
        content=body,
        media_type=content_type,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "inline",
        },
    )


@renderer_source_router.get("/v1/renderer/rig-package")
def read_renderer_rig_package(
    request: Request,
    capability: Annotated[
        str,
        Header(alias="X-Rig-Package-Capability", min_length=40, max_length=200),
    ],
) -> Response:
    service: AutoRigService | None = request.app.state.auto_rig_service
    if service is None:
        return JSONResponse(status_code=503, content={"code": "RIG_PACKAGE_NOT_CONFIGURED"})
    try:
        content_type, body, digest = service.read_package(capability)
    except AutoRigPackageUnavailable:
        return JSONResponse(
            status_code=410,
            content={"code": "RIG_PACKAGE_UNAVAILABLE", "message": "The movement package expired."},
        )
    return Response(
        content=body,
        media_type=content_type,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
            "X-Content-SHA256": digest,
        },
    )


def _execute(
    method_name: str,
    session_id: str,
    command: MobileWorkflowCommandV1,
    request: Request,
) -> JSONResponse:
    service: SupervisedFlowService | None = request.app.state.supervised_flow_service
    if service is None:
        error = SessionWorkflowError(
            code="SUPERVISED_FLOW_NOT_CONFIGURED",
            status_code=503,
            safe_message="The supervised demo flow is not configured.",
        )
        return _failure(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    if command.session_id != session_id:
        error = SessionWorkflowError(
            code="SESSION_ID_MISMATCH",
            status_code=422,
            safe_message="The path and command session identifiers must match.",
        )
        return _failure(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    method: Any = getattr(service, method_name)
    try:
        result, replayed = method(command)
    except SessionWorkflowError as error:
        return _failure(
            error,
            request_id=command.request_id,
            session_id=command.session_id,
            expected_version=command.expected_session_version,
        )
    return JSONResponse(
        status_code=200,
        content=result.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


def _failure(
    error: SessionWorkflowError,
    *,
    request_id: str,
    session_id: str,
    expected_version: int,
) -> JSONResponse:
    result = failure_result(
        request_id=request_id,
        session_id=session_id,
        expected_session_version=expected_version,
        observed_session_version=None,
        error=error,
    )
    return JSONResponse(status_code=error.status_code, content=result.model_dump(mode="json"))


__all__ = ["renderer_source_router", "router"]
