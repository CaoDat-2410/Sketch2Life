"""Pure compatibility rules for persisted Lesson Library response receipts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from sketch2life.contracts.schemas.lesson_library import (
    ParentGroupInvitationV1,
    ParentGroupMembershipV1,
)

_INVITE_SCOPE = re.compile(r"^POST /organizations/([^/]+)/parent-groups/([^/]+)/invitations$")
_ACCEPT_SCOPE = re.compile(r"^POST /me/parent-group-invitations/([^/]+)/accept$")


class ReceiptCompatibilityError(ValueError):
    """A stored response cannot be safely returned under the current contract."""


@dataclass(frozen=True, slots=True)
class ParentGroupMembershipLookup:
    membership_id: str
    parent_group_id: str
    organization_id: str
    parent_principal_ref: str | None


@dataclass(frozen=True, slots=True)
class _ResponseTarget:
    model: type[BaseModel]
    organization_id: str | None = None
    parent_group_id: str | None = None
    membership_id: str | None = None


def _response_target(operation_scope: str) -> _ResponseTarget | None:
    invite_match = _INVITE_SCOPE.fullmatch(operation_scope)
    if invite_match is not None:
        return _ResponseTarget(
            model=ParentGroupInvitationV1,
            organization_id=invite_match.group(1),
            parent_group_id=invite_match.group(2),
        )
    accept_match = _ACCEPT_SCOPE.fullmatch(operation_scope)
    if accept_match is not None:
        return _ResponseTarget(
            model=ParentGroupMembershipV1,
            membership_id=accept_match.group(1),
        )
    return None


def _response_mapping(response: object) -> dict[str, Any]:
    if not isinstance(response, Mapping) or any(not isinstance(key, str) for key in response):
        raise ReceiptCompatibilityError("stored response is not a JSON object")
    return dict(response)


def _validate_response(
    target: _ResponseTarget,
    response: Mapping[str, Any],
    *,
    revision_override: int | None = None,
) -> None:
    candidate = dict(response)
    if revision_override is not None:
        candidate["revision"] = revision_override
    try:
        target.model.model_validate(candidate)
    except ValidationError as exc:
        raise ReceiptCompatibilityError(
            "stored response does not match its current contract"
        ) from exc


def parent_group_membership_lookup(
    *,
    organization_id: str,
    principal_ref: str,
    operation_scope: str,
    response: object,
) -> ParentGroupMembershipLookup | None:
    """Return a constrained membership key only for a legacy targeted receipt."""
    response_data = _response_mapping(response)
    target = _response_target(operation_scope)
    if target is None:
        return None

    if target.organization_id is not None and target.organization_id != organization_id:
        raise ReceiptCompatibilityError("receipt organization does not match operation scope")

    if "revision" in response_data:
        _validate_response(target, response_data)
        return None

    _validate_response(target, response_data, revision_override=1)
    membership_id = response_data.get("membership_id")
    parent_group_id = response_data.get("parent_group_id")
    if not isinstance(membership_id, str) or not isinstance(parent_group_id, str):
        raise ReceiptCompatibilityError("legacy response lacks membership identity")
    if target.parent_group_id is not None and target.parent_group_id != parent_group_id:
        raise ReceiptCompatibilityError("membership group does not match operation scope")
    if target.membership_id is not None and target.membership_id != membership_id:
        raise ReceiptCompatibilityError("membership does not match operation scope")

    return ParentGroupMembershipLookup(
        membership_id=membership_id,
        parent_group_id=parent_group_id,
        organization_id=organization_id,
        parent_principal_ref=principal_ref if target.membership_id is not None else None,
    )


def upgrade_parent_group_receipt(
    *,
    operation_scope: str,
    response: object,
    membership_row: Mapping[str, Any] | None,
    organization_id: str | None = None,
    principal_ref: str | None = None,
) -> dict[str, Any]:
    """Keep current receipts unchanged or reconstruct the missing membership revision."""
    response_data = _response_mapping(response)
    target = _response_target(operation_scope)
    if target is None:
        return response_data

    if "revision" in response_data:
        _validate_response(target, response_data)
        return response_data

    _validate_response(target, response_data, revision_override=1)
    if membership_row is None:
        raise ReceiptCompatibilityError("current membership row is unavailable")
    if organization_id is None:
        raise ReceiptCompatibilityError("receipt organization is unavailable")

    membership_id = response_data.get("membership_id")
    parent_group_id = response_data.get("parent_group_id")
    row_membership_id = membership_row.get("membership_id")
    row_parent_group_id = membership_row.get("parent_group_id")
    row_organization_id = membership_row.get("organization_id")
    revision = membership_row.get("revision")
    if (
        membership_id != row_membership_id
        or parent_group_id != row_parent_group_id
        or row_organization_id != organization_id
    ):
        raise ReceiptCompatibilityError("current membership identity does not match receipt")
    if type(revision) is not int or revision < 1:
        raise ReceiptCompatibilityError("current membership revision is invalid")
    if target.membership_id is not None:
        row_principal_ref = membership_row.get("parent_principal_ref")
        if principal_ref is None or row_principal_ref != principal_ref:
            raise ReceiptCompatibilityError("current membership principal does not match receipt")

    upgraded = dict(response_data)
    upgraded["revision"] = revision
    upgraded["revision_source"] = "reconstructed_from_current_row"
    _validate_response(target, upgraded)
    return upgraded
