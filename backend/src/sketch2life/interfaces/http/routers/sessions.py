"""Versioned HTTP routes for process-local demo sessions."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from sketch2life.application.services.ephemeral_sessions import (
    DEMO_ACTOR_REF,
    EphemeralSessionService,
    SessionWorkflowError,
    failure_result,
)
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowCommandV1,
    MobileWorkflowResultV1,
)

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("", response_model=MobileWorkflowResultV1, status_code=201)
def create_session(
    command: MobileWorkflowCommandV1,
    request: Request,
) -> JSONResponse:
    service: EphemeralSessionService = request.app.state.session_service
    try:
        result, replayed = service.create(command)
    except SessionWorkflowError as error:
        result = failure_result(
            request_id=command.request_id,
            session_id=command.session_id,
            expected_session_version=command.expected_session_version,
            observed_session_version=None,
            error=error,
        )
        return JSONResponse(
            status_code=error.status_code,
            content=result.model_dump(mode="json"),
        )
    return JSONResponse(
        status_code=200 if replayed else 201,
        content=result.model_dump(mode="json"),
        headers={"Idempotency-Replayed": str(replayed).lower()},
    )


@router.get("/{session_id}", response_model=MobileWorkflowResultV1)
def get_session(
    session_id: str,
    request: Request,
    request_id: Annotated[str, Header(alias="X-Request-ID", min_length=1, max_length=120)],
    expected_session_version: Annotated[int, Header(alias="X-Expected-Session-Version", ge=0)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)],
    actor_ref: Annotated[str, Header(alias="X-Actor-Ref", min_length=1, max_length=160)],
) -> JSONResponse:
    del idempotency_key  # Trace metadata only on reads; read requests do not mutate state.
    service: EphemeralSessionService = request.app.state.session_service
    if actor_ref != DEMO_ACTOR_REF:
        error = SessionWorkflowError(
            code="DEMO_ACTOR_INVALID",
            status_code=422,
            safe_message="The local demo actor marker is invalid.",
        )
        result = failure_result(
            request_id=request_id,
            session_id=session_id,
            expected_session_version=expected_session_version,
            observed_session_version=None,
            error=error,
        )
        return JSONResponse(status_code=error.status_code, content=result.model_dump(mode="json"))
    try:
        result = service.read(
            session_id=session_id,
            request_id=request_id,
            expected_session_version=expected_session_version,
        )
    except SessionWorkflowError as error:
        result = failure_result(
            request_id=request_id,
            session_id=session_id,
            expected_session_version=expected_session_version,
            observed_session_version=None,
            error=error,
        )
        return JSONResponse(status_code=error.status_code, content=result.model_dump(mode="json"))
    return JSONResponse(status_code=200, content=result.model_dump(mode="json"))


__all__ = ["router"]
