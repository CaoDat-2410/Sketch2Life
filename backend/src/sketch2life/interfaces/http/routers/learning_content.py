"""CMD-48 content transport seam, not production composition or full dispatcher.

Identity/scope resolution is mandatory and server-injected, never a demo header.
Preset/policy schemas/delegates remain an explicit C4 gate. No read/delivery route
is added: BE1 CMD-59/60 consumes the application eligibility projection instead.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.contracts.schemas.ai_jobs import CollaborationErrorV1, ErrorBodyV1
from sketch2life.contracts.schemas.learning_content import CONTENT_COMMAND_ADAPTER
from sketch2life.domain.learning_content.model import ContentError

_ID = re.compile(r"[A-Za-z0-9_.:-]{1,120}\Z")
_MATCH = re.compile(r'"([1-9][0-9]{0,18})"\Z')
_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}


@dataclass(frozen=True, slots=True)
class GovernanceIdentity:
    """Scope selected by verified server context; not request-body/header claims."""

    principal_id: str
    organization_id: str


IdentityResolver = Callable[[Request], GovernanceIdentity | None]

_ERROR_STATUS = {
    "CONTENT_FORBIDDEN": 403,
    "CONTENT_SEPARATION_REQUIRED": 403,
    "CONTENT_NOT_FOUND": 404,
    "CONTENT_PRECONDITION_REQUIRED": 428,
    "CONTENT_UNEXPECTED_PRECONDITION": 400,
    "CONTENT_STALE_REVISION": 409,
    "CONTENT_STALE_REVIEW": 409,
    "CONTENT_COMMAND_CONFLICT": 409,
    "CONTENT_WRITE_CONFLICT": 409,
    "CONTENT_SUPERSEDED_VERSION": 409,
    "CONTENT_HASH_MISMATCH": 409,
    "CONTENT_REVIEW_REQUIRED": 409,
    "CONTENT_REVIEW_MISMATCH": 409,
    "CONTENT_REVIEW_INEFFECTIVE": 409,
    "CONTENT_RECEIPT_INEFFECTIVE": 409,
    "CONTENT_TRANSITION_DENIED": 409,
    "CONTENT_POLICY_DENIED": 403,
    "CONTENT_SOURCE_DENIED": 403,
    "CONTENT_SOURCE_AUTHORITY_REQUIRED": 503,
    "CONTENT_DEPENDENCY_UNAVAILABLE": 503,
    "CONTENT_REASON_REQUIRED": 422,
}


def _error(correlation: str, status: int, code: str) -> JSONResponse:
    envelope = CollaborationErrorV1(
        correlation_id=correlation,
        error=ErrorBodyV1(code=code, message="Governance command was not accepted.",
                          retryable=status == 503))
    return JSONResponse(envelope.model_dump(mode="json"), status_code=status, headers=_HEADERS)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError("non-JSON number")


def _request_schema() -> dict[str, object]:
    # Inline this finite, non-recursive DTO graph so the manually parsed body
    # still has a complete OpenAPI contract without unresolved $defs references.
    schema = CONTENT_COMMAND_ADAPTER.json_schema()
    definitions = schema.pop("$defs", {})

    def expand(value: object) -> object:
        if isinstance(value, dict):
            if "$ref" in value:
                return expand(definitions[value["$ref"].split("/")[-1]])
            return {key: expand(item) for key, item in value.items() if key != "discriminator"}
        if isinstance(value, list):
            return [expand(item) for item in value]
        return value

    # Mapping strings in the discriminator reference component names; inline
    # oneOf schemas suffice, without a misleading mapping to absent components.
    schema.pop("discriminator", None)
    result = expand(schema)
    assert isinstance(result, dict)
    return result


def build_content_commands_router(
    service: ContentCommands, resolve_identity: IdentityResolver, *,
    max_body_bytes: int, prefix: str = "/api/collaboration/v1",
) -> APIRouter:
    """One candidate command route. Caller supplies transport admission limit.

    No default identity, no default production policy, no registration in the
    default application until real owner adapters/closed delegates are adopted.
    """
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ValueError("positive transport admission limit required")
    router = APIRouter(prefix=prefix, tags=["governance-content-candidate"])

    @router.post("/governance/records", response_model=None, openapi_extra={
        "requestBody": {"required": True, "content": {
            "application/json": {"schema": _request_schema()}}},
        "description": "Candidate content branch only; owner delegates not adopted.",
        "parameters": [{"name": "If-Match", "in": "header", "required": False,
                        "schema": {"type": "string"},
                        "description": 'Strong quoted record revision; omit for create.'}],
    })
    async def command(request: Request) -> JSONResponse:
        supplied = request.headers.get("x-correlation-id", "")
        correlation = supplied if _ID.fullmatch(supplied) else "corr_" + uuid4().hex
        try:
            identity = await run_in_threadpool(resolve_identity, request)
            if identity is None:
                return _error(correlation, 401, "UNAUTHENTICATED")
            if (not _ID.fullmatch(identity.principal_id)
                    or not _ID.fullmatch(identity.organization_id)):
                return _error(correlation, 503, "CONTENT_DEPENDENCY_UNAVAILABLE")
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != (
                "application/json"
            ):
                return _error(correlation, 415, "UNSUPPORTED_MEDIA_TYPE")
            expected = None
            supplied_match = request.headers.get("if-match")
            if supplied_match is not None:
                match = _MATCH.fullmatch(supplied_match)
                if match is None or int(match[1]) > 2**63 - 1:
                    return _error(correlation, 400, "MALFORMED_PRECONDITION")
                expected = int(match[1])
            raw = bytearray()
            async for chunk in request.stream():
                if len(raw) + len(chunk) > max_body_bytes:
                    return _error(correlation, 413, "REQUEST_TOO_LARGE")
                raw.extend(chunk)
            try:
                # Reject ambiguous duplicate fields and NaN before strict DTO
                # validation. Never return Pydantic input/errors containing body.
                json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_invalid_constant)
                payload = CONTENT_COMMAND_ADAPTER.validate_json(raw)
            except (ValueError, UnicodeError, ValidationError, RecursionError):
                return _error(correlation, 422, "INVALID_GOVERNANCE_COMMAND")
            result = await run_in_threadpool(
                service.execute, identity.principal_id, identity.organization_id,
                payload, expected_revision=expected)
            return JSONResponse(
                {"correlation_id": correlation, "data": result.model_dump(mode="json")},
                headers={**_HEADERS, "ETag": f'"{result.current_revision}"'})
        except ContentError as error:
            code = str(error)
            if code not in _ERROR_STATUS:
                return _error(correlation, 503, "CONTENT_DEPENDENCY_UNAVAILABLE")
            return _error(correlation, _ERROR_STATUS[code], code)
        except Exception:
            # Adapters may carry DSNs/tokens/body text in exception messages.
            # Do not expose or log their raw exception in this transport seam.
            return _error(correlation, 500, "INTERNAL_ERROR")

    return router
