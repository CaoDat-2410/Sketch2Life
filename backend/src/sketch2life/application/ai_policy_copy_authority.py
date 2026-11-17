"""Strict current copy-authority grant validation shared by own application components."""

from datetime import datetime

from sketch2life.contracts.schemas.ai_policy_copy import CopyAuthorityGrant
from sketch2life.domain.ai_policy.model import PolicyError


def validate_copy_grant(
    grant: CopyAuthorityGrant, principal: str, organization: str, digest: str, now: datetime
) -> CopyAuthorityGrant:
    try:
        grant = CopyAuthorityGrant.model_validate(grant.model_dump(mode="python"), strict=True)
        if now.utcoffset() is None:
            raise ValueError("naive clock")
    except (TypeError, ValueError, AttributeError):
        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH") from None
    if (grant.principal_id, grant.organization_id, grant.command_digest) != (
        principal,
        organization,
        digest,
    ):
        raise PolicyError("AI_POLICY_COPY_AUTHORITY_MISMATCH")
    if grant.allowed is not True:
        raise PolicyError("AI_POLICY_FORBIDDEN")
    if grant.expires_at <= now:
        raise PolicyError("AI_POLICY_COPY_AUTHORITY_EXPIRED")
    return grant
