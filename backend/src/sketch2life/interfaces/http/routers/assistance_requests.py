"""CMD-32 / CMD-33 thin candidate adapters (BE2-03 A1, fixture composition only).

Transport only: the principal resolver is injected, bodies are parsed strictly against the
0.1-candidate contracts (unknown fields such as role/org/status/audience are refused), and the
application service owns disclosure, receipts, turn/scope/consent/age, limits and CAS. The
projection (Teacher record or minimal device view) follows the verified principal. Never
mounted by the production app; there is no GET route in A1.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from sketch2life.application.ports.ai_jobs import Principal, PrincipalRole
from sketch2life.application.services.assistance import (
    AssistanceError,
    AssistanceService,
    CancelCommand,
    CommandResult,
    SubmitCommand,
    device_view,
    teacher_view,
)
from sketch2life.contracts.schemas.ai_jobs import CollaborationErrorV1, ErrorBodyV1, FieldErrorV1
from sketch2life.contracts.schemas.assistance_requests import (
    AssistanceCancelCommandV1,
    AssistanceReceiptEnvelopeV1,
    AssistanceRequestCommandV1,
    IndividualTargetV1,
)
from sketch2life.domain.assistance import (
    CheckpointRef,
    RequestReason,
    TargetKind,
    TargetScope,
)

CANDIDATE_PREFIX = "/api/collaboration/v1"
MAX_BODY_BYTES = 32 * 1024
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_CACHE_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}
_MAX_FIELD_ERRORS = 16

PrincipalResolver = Callable[[Request], Principal | None]


def build_assistance_requests_router(
    service: AssistanceService,
    resolve_principal: PrincipalResolver,
    *,
    prefix: str = CANDIDATE_PREFIX,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["assistance-requests-candidate"])

    @router.post("/assistance-requests", response_model=None)
    async def submit(request: Request) -> Response:
        correlation_id = _correlation_id(request)
        principal, key, body, failure = await _preamble(request, correlation_id)
        if failure is not None:
            return failure
        assert principal is not None and body is not None
        try:
            parsed = AssistanceRequestCommandV1.model_validate_json(body)
        except ValidationError as exc:
            return _validation_error(correlation_id, exc)
        target = parsed.target_scope
        command = SubmitCommand(
            principal=principal,
            idempotency_key=key,
            canvas_id=parsed.canvas_id,
            checkpoint_ref=CheckpointRef(
                parsed.checkpoint_ref.checkpoint_id, parsed.checkpoint_ref.document_epoch,
                parsed.checkpoint_ref.server_sequence, parsed.checkpoint_ref.hash),
            target=(TargetScope(TargetKind.INDIVIDUAL, target.participant_id)
                    if isinstance(target, IndividualTargetV1)
                    else TargetScope(TargetKind.GROUP, target.group_id)),
            region_id=parsed.target_region_id,
            requested_level=parsed.requested_level,
            child_intent=parsed.child_intent,
            request_reason=RequestReason(parsed.request_reason),
            context_revision=parsed.context_revision,
            client_request_id=parsed.client_request_id,
            correlation_id=correlation_id,
        )
        try:
            result = service.submit(command)
        except AssistanceError as exc:
            return _service_error(correlation_id, exc)
        return _receipt(service, principal, result, correlation_id, status_code=202)

    @router.post("/assistance-requests/{assistance_id}/cancel", response_model=None)
    async def cancel(assistance_id: str, request: Request) -> Response:
        correlation_id = _correlation_id(request)
        if not _ID.match(assistance_id):
            return _error(correlation_id, 400, "MALFORMED_REQUEST", "Malformed id.")
        principal, key, body, failure = await _preamble(request, correlation_id)
        if failure is not None:
            return failure
        assert principal is not None and body is not None
        try:
            parsed = AssistanceCancelCommandV1.model_validate_json(body)
        except ValidationError as exc:
            return _validation_error(correlation_id, exc)
        try:
            result = service.cancel(CancelCommand(principal, assistance_id, key,
                                                  request.headers.get("if-match"),
                                                  parsed.reason))
        except AssistanceError as exc:
            return _service_error(correlation_id, exc)
        return _receipt(service, principal, result, correlation_id, status_code=200)

    async def _preamble(
        request: Request, correlation_id: str
    ) -> tuple[Principal | None, str | None, bytes | None, Response | None]:
        principal = resolve_principal(request)
        if principal is None:
            return None, None, None, _error(correlation_id, 401, "UNAUTHENTICATED",
                                            "Authentication required.")
        key = request.headers.get("idempotency-key")
        if not key or not _ID.match(key):
            return None, None, None, _error(correlation_id, 400, "MALFORMED_REQUEST",
                                            "Idempotency-Key is required.")
        media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if media_type != "application/json":
            return None, None, None, _error(correlation_id, 415, "UNSUPPORTED_MEDIA_TYPE",
                                            "Send application/json.")
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return None, None, None, _error(correlation_id, 413, "PAYLOAD_TOO_LARGE",
                                            "The request is too large.")
        return principal, key, body, None

    return router


def _receipt(service: AssistanceService, principal: Principal, result: CommandResult,
             correlation_id: str, *, status_code: int) -> JSONResponse:
    request = result.request
    teacher = principal.role is PrincipalRole.TEACHER
    data = teacher_view(request) if teacher else device_view(request, service.poll_after_ms)
    envelope = AssistanceReceiptEnvelopeV1.model_validate_json(json.dumps({
        "correlation_id": correlation_id,
        "data": data,
        "meta": {"outcome": str(result.outcome), "replayed": result.replayed,
                 "resource_revision": request.request_revision,
                 "projection": "teacher" if teacher else "device"},
    }))
    headers = {"ETag": request.etag(), **_CACHE_HEADERS}
    if result.replayed:
        headers["Idempotency-Replayed"] = "true"
    return JSONResponse(envelope.model_dump(mode="json"), status_code=status_code,
                        headers=headers)


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get("x-correlation-id")
    if supplied and _ID.match(supplied):
        return supplied
    return f"corr_{uuid4().hex}"


def _service_error(correlation_id: str, exc: AssistanceError) -> JSONResponse:
    revisions = None if exc.current_revision is None else {"assistance": exc.current_revision}
    response = _error(correlation_id, exc.http_status, exc.code, exc.public_message,
                      retryable=exc.retryable, current_revisions=revisions)
    if exc.retry_after_s is not None:
        response.headers["Retry-After"] = str(exc.retry_after_s)
    return response


def _validation_error(correlation_id: str, exc: ValidationError) -> JSONResponse:
    errors = exc.errors(include_input=False, include_url=False)
    if any(error["type"] == "json_invalid" for error in errors):
        return _error(correlation_id, 400, "MALFORMED_REQUEST", "Malformed JSON body.")
    extra = any(error["type"] == "extra_forbidden" for error in errors)
    field_errors = tuple(
        FieldErrorV1(
            path=(".".join(str(part) for part in error["loc"]) or "body")[:200],
            rule=str(error["type"])[:80],
            message="Field not allowed." if error["type"] == "extra_forbidden"
            else "Invalid value.",
        )
        for error in errors[:_MAX_FIELD_ERRORS]
    )
    code = "FIELD_NOT_ALLOWED" if extra else "FIELD_VALIDATION_FAILED"
    return _error(correlation_id, 422, code, "The request has invalid fields.",
                  field_errors=field_errors)


def _error(
    correlation_id: str,
    status: int,
    code: str,
    message: str,
    *,
    retryable: bool = False,
    field_errors: tuple[FieldErrorV1, ...] = (),
    current_revisions: dict[str, int] | None = None,
) -> JSONResponse:
    body = CollaborationErrorV1(
        correlation_id=correlation_id,
        error=ErrorBodyV1(code=code, message=message, retryable=retryable,
                          field_errors=field_errors, current_revisions=current_revisions),
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=status, headers=_CACHE_HEADERS)


__all__ = ["CANDIDATE_PREFIX", "MAX_BODY_BYTES", "PrincipalResolver",
           "build_assistance_requests_router"]
