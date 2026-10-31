from __future__ import annotations

import pytest
from sketch2life.contracts.schemas.assistance_requests import ConsentRevisionRefV1
from sketch2life.domain.assistance import AssistanceRuleViolation, MemberFact


def _member(**overrides: object) -> MemberFact:
    values: dict[str, object] = {
        "participant_id": "child-1",
        "completed_age_months": 60,
        "age_provenance_ref": "age-source-1",
        "age_revision": 1,
        "consent_record_ref": "consent-1",
        "consent_revision": 1,
        "consent_effective": True,
        "purpose_granted": True,
    }
    values.update(overrides)
    return MemberFact(**values)  # type: ignore[arg-type]


def test_synthetic_member_fact_requires_both_consent_values_to_be_none() -> None:
    member = _member(
        consent_record_ref=None,
        consent_revision=None,
        consent_effective=False,
        purpose_granted=False,
        eligibility_basis="SYNTHETIC_DEV",
    )
    assert member.consent_record_ref is None
    assert member.consent_revision is None


@pytest.mark.parametrize(
    "changes",
    (
        {"consent_record_ref": None},
        {"consent_revision": None},
        {"consent_record_ref": None, "consent_revision": None},
    ),
)
def test_legal_or_legacy_member_fact_requires_both_consent_values(
    changes: dict[str, object],
) -> None:
    with pytest.raises(AssistanceRuleViolation):
        _member(**changes)


def test_synthetic_member_fact_rejects_any_fabricated_consent_value() -> None:
    with pytest.raises(AssistanceRuleViolation):
        _member(
            consent_effective=False,
            purpose_granted=False,
            eligibility_basis="SYNTHETIC_DEV",
        )


def test_teacher_consent_reference_allows_null_pair_only_for_synthetic_basis() -> None:
    value = ConsentRevisionRefV1.model_validate(
        {
            "participant_id": "child-1",
            "consent_record_ref": None,
            "revision": None,
            "eligibility_basis": "SYNTHETIC_DEV",
        }
    )
    assert value.consent_record_ref is None and value.revision is None

    legal = ConsentRevisionRefV1.model_validate(
        {
            "participant_id": "child-1",
            "consent_record_ref": "consent-1",
            "revision": 2,
        }
    )
    assert legal.consent_record_ref == "consent-1" and legal.revision == 2


@pytest.mark.parametrize(
    "value",
    (
        {"participant_id": "child-1", "consent_record_ref": None, "revision": None},
        {
            "participant_id": "child-1",
            "consent_record_ref": None,
            "revision": None,
            "eligibility_basis": "LEGAL_CONSENT",
        },
        {
            "participant_id": "child-1",
            "consent_record_ref": "consent-1",
            "revision": None,
            "eligibility_basis": "SYNTHETIC_DEV",
        },
        {
            "participant_id": "child-1",
            "consent_record_ref": None,
            "revision": 1,
            "eligibility_basis": "SYNTHETIC_DEV",
        },
    ),
)
def test_teacher_dto_rejects_missing_legal_or_mixed_synthetic_consent(
    value: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ConsentRevisionRefV1.model_validate(value)
