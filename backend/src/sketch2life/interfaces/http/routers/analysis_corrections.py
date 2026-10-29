"""CMD-34 ``POST /analysis-results/{analysis_id}/corrections`` thin adapter (BE2-02 C1).

Transport only: the principal resolver is injected, the body is parsed strictly against the
DATA-22 correction candidate (unknown fields such as author/role/status are refused), and the
application service owns disclosure, replay, turn, eligibility, If-Match and CAS. The response
is the Teacher or Child-device projection chosen from the verified principal. Fixture
composition only; never mounted by the production app, and there is no GET route.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from uuid import uuid4

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.services.vision_analysis import (
    CorrectionCommand,
    VisionAnalysisError,
    VisionAnalysisService,
    child_correction_view,
    teacher_correction_view,
)
from sketch2life.contracts.schemas.ai_jobs import CollaborationErrorV1, ErrorBodyV1, FieldErrorV1
from sketch2life.contracts.schemas.analysis_results import (
    AnalysisCorrectionChildEnvelopeV1,
    AnalysisCorrectionCommandV1,
    AnalysisCorrectionEnvelopeV1,
)
from sketch2life.domain.vision_analysis import ActorRole

CANDIDATE_PREFIX = "/api/collaboration/v1"
MAX_BODY_BYTES = 32 * 1024
_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,120}$")
_CACHE_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}
_MAX_FIELD_ERRORS = 16

PrincipalResolver = Callable[[Request], Principal | None]


def build_analysis_corrections_router(
    service: VisionAnalysisService,
    resolve_principal: PrincipalResolver,
    *,
    prefix: str = CANDIDATE_PREFIX,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["analysis-corrections-candidate"])

    @router.post("/analysis-results/{analysis_id}/corrections", response_model=None)
    async def submit_correction(analysis_id: str, request: Request) -> Response:
        correlation_id = _correlation_id(request)
        principal = resolve_principal(request)
        if principal is None:
            return _error(correlation_id, 401, "UNAUTHENTICATED", "Authentication required.")
        if not _ID.match(analysis_id):
            return _error(correlation_id, 400, "MALFORMED_REQUEST", "Malformed analysis id.")
        key = request.headers.get("idempotency-key")
        if not key or not _ID.match(key):
            return _error(correlation_id, 400, "MALFORMED_REQUEST",
                          "Idempotency-Key is required.")
        media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
        if media_type != "application/json":
            return _error(correlation_id, 415, "UNSUPPORTED_MEDIA_TYPE",
                          "Send application/json.")
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return _error(correlation_id, 413, "PAYLOAD_TOO_LARGE", "The request is too large.")
        try:
            parsed = AnalysisCorrectionCommandV1.model_validate_json(body)
        except ValidationError as exc:
            return _validation_error(correlation_id, exc)
        command = CorrectionCommand(
            principal=principal,
            analysis_id=analysis_id,
            idempotency_key=key,
            if_match=request.headers.get("if-match"),
            intended_objects=parsed.intended_objects,
            correction_reason=parsed.correction_reason,
            expected_context_revision=parsed.expected_context_revision,
            child_explanation=parsed.child_explanation,
            basis_correction_ref=parsed.basis_correction_ref,
        )
        try:
            result = service.submit_correction(command)
        except VisionAnalysisError as exc:
            revisions = (
                None if exc.current_revision is None else {"analysis": exc.current_revision}
            )
            return _error(correlation_id, exc.http_status, exc.code, exc.public_message,
                          retryable=exc.retryable, current_revisions=revisions)
        headers = {"ETag": result.etag, **_CACHE_HEADERS}
        if result.replayed:
            headers["Idempotency-Replayed"] = "true"
        meta = {
            "resource_revision": result.receipt.analysis_revision_after,
            "projection": str(result.role),
            "replayed": result.replayed,
        }
        envelope: AnalysisCorrectionEnvelopeV1 | AnalysisCorrectionChildEnvelopeV1
        if result.role is ActorRole.CHILD_DEVICE:
            envelope = AnalysisCorrectionChildEnvelopeV1.model_validate_json(json.dumps(
                {"correlation_id": correlation_id, "data": child_correction_view(result),
                 "meta": meta}
            ))
        else:
            envelope = AnalysisCorrectionEnvelopeV1.model_validate_json(json.dumps(
                {"correlation_id": correlation_id, "data": teacher_correction_view(result),
                 "meta": meta}
            ))
        return JSONResponse(envelope.model_dump(mode="json"), headers=headers)

    return router


def _correlation_id(request: Request) -> str:
    supplied = request.headers.get("x-correlation-id")
    if supplied and _ID.match(supplied):
        return supplied
    return f"corr_{uuid4().hex}"


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
           "build_analysis_corrections_router"]
