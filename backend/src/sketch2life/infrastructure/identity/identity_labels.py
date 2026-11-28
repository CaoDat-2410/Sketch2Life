"""Privacy-safe labels for adult accounts resolved at the infrastructure boundary."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sketch2life.application.ports.identity import IdentityAccountProvisioningUnavailable


def safe_display_name(value: str | None, *, subject: str | None = None) -> str | None:
    """Return a human label without echoing an e-mail or sign-in subject."""
    if not isinstance(value, str):
        return None
    name = value.strip()
    if not name or "@" in name or (subject and name.casefold() == subject.strip().casefold()):
        return None
    return name


def masked_email(value: str | None) -> str | None:
    """Mask the local part using the existing Teacher-candidate convention."""
    if not isinstance(value, str) or any(character.isspace() for character in value):
        return None
    local, separator, domain = value.partition("@")
    if not separator or not local or not domain:
        return None
    return f"{local[:2]}***@{domain}"


def account_profiles(provisioner: Any, subjects: Iterable[str]) -> dict[str, Any]:
    """Read profiles in provider-sized batches; presentation degrades to role-only labels."""
    unique_subjects = list(dict.fromkeys(subject for subject in subjects if subject))
    if provisioner is None or not unique_subjects:
        return {}

    profiles: dict[str, Any] = {}
    try:
        for offset in range(0, len(unique_subjects), 100):
            profiles.update(
                provisioner.get_account_profiles(unique_subjects[offset : offset + 100])
            )
    except IdentityAccountProvisioningUnavailable:
        return {}
    return profiles


def teacher_identity_fields(profile: Any | None) -> dict[str, str | None]:
    """Fields shared with the existing Teacher-candidate label contract."""
    return {
        "display_name": safe_display_name(
            getattr(profile, "display_name", None),
            subject=getattr(profile, "subject", None),
        ),
        "email_masked": masked_email(getattr(profile, "email", None)),
    }


def teacher_identity_label(fields: dict[str, str | None]) -> str:
    parts = [fields.get("display_name"), fields.get("email_masked")]
    visible = [part for part in parts if part]
    return " · ".join(visible) if visible else "Teacher chưa có tên hiển thị"
