"""Pure rules of the Teacher profile revisions (FEAT-066 goal v4 T-12b).

A revision is one immutable snapshot of the fields a Teacher may edit on a managed profile: the
display name, the age in months with its versioned age band, and a bounded list of structured
interests (SRS l.497 FR-C-05, l.829; REG l.272, l.335). Nothing here touches a database, a clock
or a secret. The migration ``20261121_bpr_0001`` carries a byte-for-byte copy of the hash and the
baseline-id functions (a migration must not import application code); a unit test pins the two
copies equal.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
import uuid
from collections.abc import Iterable, Sequence

from sketch2life.domain.diagnosis_screen import looks_like_diagnosis

HASH_DOMAIN = "be1.profile.revision"
HASH_VERSION = 1
BAND_VERSION = 1
# The author recorded on a baseline created by the migration (a provenance marker, not a person).
LEGACY_AUTHOR = "LEGACY_UNCLASSIFIED"

MIN_AGE_MONTHS = 36
MAX_EDIT_AGE_MONTHS = 120  # a new value never exceeds 120 months (AC-62, l.2731)
MAX_STORED_AGE_MONTHS = 155  # legacy rows may hold up to 155 months and are preserved as they are

INTEREST_MAX_ITEMS = 20
INTEREST_MAX_CHARACTERS = 80
INTEREST_MAX_BYTES = 320

BAND_36_71 = "AGE_36_71"
BAND_72_107 = "AGE_72_107"
BAND_108_120 = "AGE_108_120"
BAND_CODES = (BAND_36_71, BAND_72_107, BAND_108_120)

_BASELINE_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, "urn:sketch2life:be1:profile-revision-baseline:v1"
)


class ProfileRevisionRuleViolation(ValueError):
    """A revision value breaks a rule; ``code`` is a machine code that carries no child value."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def age_band(age_months: int) -> tuple[int, str] | None:
    """The versioned age band of an age, or ``None`` above 120 months (a quarantined legacy age).

    The bands are the accepted 36-71, 72-107 and 108-120 ranges of AC-62 (SRS l.2731). An age
    below 36 is not a stored value and is refused.
    """
    if age_months < MIN_AGE_MONTHS:
        raise ProfileRevisionRuleViolation("AGE_OUT_OF_RANGE", "age is below the supported range")
    if age_months <= 71:
        return BAND_VERSION, BAND_36_71
    if age_months <= 107:
        return BAND_VERSION, BAND_72_107
    if age_months <= MAX_EDIT_AGE_MONTHS:
        return BAND_VERSION, BAND_108_120
    return None


# Control, surrogate, line and paragraph separator characters (T-12a policy, widened to the
# Unicode categories so C1 controls and U+2028 and U+2029 are refused too).
_REFUSED_CATEGORIES = frozenset({"Cc", "Cs", "Zl", "Zp"})


def has_control_character(value: str) -> bool:
    return any(unicodedata.category(char) in _REFUSED_CATEGORIES for char in value)


def normalize_interests(values: Iterable[str]) -> tuple[str, ...]:
    """Validate and normalise the structured interests (OPEN-3 default, an owner-reviewable bound).

    Each item is NFC-normalised and trimmed, then must be 1 to 80 characters and at most 320
    UTF-8 bytes, with no control character (a newline or a tab too); the list holds at most 20
    items and no duplicate (after normalisation). The order is kept. There is no vocabulary: the
    items are free short labels, never a diagnosis (BR-20 screen), a note or a support need.
    """
    items = [unicodedata.normalize("NFC", value).strip() for value in values]
    if len(items) > INTEREST_MAX_ITEMS:
        raise ProfileRevisionRuleViolation("TOO_MANY", "too many interests")
    for item in items:
        if not item:
            raise ProfileRevisionRuleViolation("EMPTY", "an interest is empty")
        if len(item) > INTEREST_MAX_CHARACTERS or len(item.encode("utf-8")) > INTEREST_MAX_BYTES:
            raise ProfileRevisionRuleViolation("TOO_LONG", "an interest is too long")
        if has_control_character(item):
            raise ProfileRevisionRuleViolation("INVALID_FORMAT", "an interest has a control char")
        if looks_like_diagnosis(item):
            # BR-20 (SRS l.266): an interest never carries a diagnosis; the text is not echoed.
            raise ProfileRevisionRuleViolation("DIAGNOSIS_LIKE", "an interest names a diagnosis")
    if len(set(items)) != len(items):
        raise ProfileRevisionRuleViolation("DUPLICATE", "an interest is repeated")
    return tuple(items)


def canonical_revision_bytes(
    *,
    child_id: str,
    revision_no: int,
    display_name: str,
    age_months: int,
    structured_interests: Sequence[str],
) -> bytes:
    """Versioned canonical UTF-8 JSON of a revision (sorted keys, no spaces, no ASCII escaping).

    It holds the domain, the hash version, the profile id, the revision number, the allowed data
    and the age band. It holds neither a timestamp nor the author, so the same content always
    has the same hash and a re-read never changes it.
    """
    band = age_band(age_months)
    return json.dumps(
        {
            "domain": HASH_DOMAIN,
            "v": HASH_VERSION,
            "child_id": child_id,
            "revision_no": revision_no,
            "display_name": display_name,
            "age_months": age_months,
            "age_band": None if band is None else {"version": band[0], "code": band[1]},
            "structured_interests": list(structured_interests),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def revision_hash(
    *,
    child_id: str,
    revision_no: int,
    display_name: str,
    age_months: int,
    structured_interests: Sequence[str],
) -> str:
    """Lowercase SHA-256 hex (64 characters) of the canonical revision."""
    return hashlib.sha256(
        canonical_revision_bytes(
            child_id=child_id,
            revision_no=revision_no,
            display_name=display_name,
            age_months=age_months,
            structured_interests=structured_interests,
        )
    ).hexdigest()


def baseline_revision_id(child_id: str) -> str:
    """The deterministic id of revision 1 of a profile (backfill and every new profile)."""
    return str(uuid.uuid5(_BASELINE_NAMESPACE, child_id))


__all__ = [
    "BAND_CODES",
    "BAND_VERSION",
    "HASH_DOMAIN",
    "HASH_VERSION",
    "INTEREST_MAX_BYTES",
    "INTEREST_MAX_CHARACTERS",
    "INTEREST_MAX_ITEMS",
    "LEGACY_AUTHOR",
    "MAX_EDIT_AGE_MONTHS",
    "MAX_STORED_AGE_MONTHS",
    "MIN_AGE_MONTHS",
    "ProfileRevisionRuleViolation",
    "age_band",
    "baseline_revision_id",
    "has_control_character",
    "canonical_revision_bytes",
    "normalize_interests",
    "revision_hash",
]
