"""Read the current synthetic-only Parent consent-policy placeholder (T-CONSENT1)."""

# FastAPI dependency declarations intentionally use Depends in defaults.
# ruff: noqa: B008

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import (
    ParentRoleReader,
    ParentRoleStoreUnavailable,
)
from sketch2life.contracts.schemas.parent_consent_policy import ParentConsentPolicyV1
from sketch2life.domain.parent_consent_policy import CURRENT_PARENT_CONSENT_POLICY
from sketch2life.infrastructure.persistence.be1_parent_role_adapter import Be1ParentRoleAdapter
from sketch2life.interfaces.http.be1_runtime import Be1Runtime, get_runtime, get_verified_adult
from sketch2life.interfaces.http.error_envelope import PARENT_CONSENT_POLICY_PATH

router = APIRouter(tags=["Parent Profiles"])
_READ_HEADERS = {"Cache-Control": "private, no-cache", "Vary": "Authorization"}


def get_consent_role_reader(
    runtime: Be1Runtime = Depends(get_runtime),
) -> ParentRoleReader:
    session_factory = runtime.session_factory
    if session_factory is None:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_NOT_CONFIGURED"}) from None
    return Be1ParentRoleAdapter(session_factory)


def _require_active_parent(
    principal: VerifiedPrincipal, role_reader: ParentRoleReader
) -> None:
    try:
        active_parent = role_reader.has_active_parent_role(principal=principal)
    except ParentRoleStoreUnavailable:
        raise HTTPException(status_code=503, detail={"code": "DATABASE_UNAVAILABLE"}) from None
    if not active_parent:
        raise HTTPException(status_code=403, detail={"code": "ACTION_NOT_ALLOWED"}) from None


@router.get(
    PARENT_CONSENT_POLICY_PATH,
    response_model=ParentConsentPolicyV1,
    operation_id="parentGetConsentPolicyV1",
    summary="Read the current synthetic-only Parent consent-policy placeholder",
)
def get_parent_consent_policy(
    request: Request,
    response: Response,
    principal: VerifiedPrincipal = Depends(get_verified_adult),
    role_reader: ParentRoleReader = Depends(get_consent_role_reader),
) -> dict[str, Any]:
    _require_active_parent(principal, role_reader)
    for name, value in _READ_HEADERS.items():
        response.headers[name] = value

    policy = CURRENT_PARENT_CONSENT_POLICY
    request_id = getattr(request.state, "be1_request_id", None)
    if not isinstance(request_id, str) or not request_id:
        request_id = str(uuid4())
    return {
        "contract": "ParentConsentPolicyV1",
        "request_id": request_id,
        "policy": {
            "purpose_code": policy.purpose_code,
            "policy_version": policy.policy_version,
            "consent_text": policy.consent_text,
            "consent_text_sha256": policy.consent_text_sha256,
            "policy_state": policy.policy_state,
            "data_origin_scope": policy.data_origin_scope,
            "effective_from": policy.effective_from,
            "purposes": [
                {"purpose_code": purpose_code, "text_key": text_key}
                for purpose_code, text_key in policy.purposes
            ],
            "links": list(policy.links),
            "acceptance_recording": policy.acceptance_recording,
        },
    }
