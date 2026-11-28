"""Immutable synthetic-only Parent consent-policy placeholder (T-CONSENT1).

The text quotes BR-27 from the current working SRS. It is a placeholder notice, not approved legal
text; real-data consent remains unavailable while OI-05 is open.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256

_CONSENT_TEXT = (
    "Mọi luồng demo chỉ dùng profile, tranh và audio tổng hợp. Dữ liệu trẻ thật nằm ngoài demo, "
    "cần chính sách riêng về mục đích, quyền, phân quyền, chuyển dữ liệu cho provider và lifecycle."
)


@dataclass(frozen=True, slots=True)
class ParentConsentPolicy:
    purpose_code: str
    policy_version: str
    consent_text: str
    consent_text_sha256: str
    policy_state: str
    data_origin_scope: str
    effective_from: date | None
    purposes: tuple[tuple[str, str], ...]
    links: tuple[str, ...]
    acceptance_recording: str


CURRENT_PARENT_CONSENT_POLICY = ParentConsentPolicy(
    purpose_code="SYNTHETIC_TEST_ONLY",
    policy_version="parent-consent-placeholder-v0",
    consent_text=_CONSENT_TEXT,
    consent_text_sha256=sha256(_CONSENT_TEXT.encode("utf-8")).hexdigest(),
    policy_state="PLACEHOLDER_NOT_APPROVED",
    data_origin_scope="SYNTHETIC_TEST",
    effective_from=None,
    purposes=(
        (
            "SYNTHETIC_TEST_ONLY",
            "parent.consent.placeholder.synthetic_test_only",
        ),
    ),
    links=(),
    acceptance_recording="NOT_AVAILABLE",
)
