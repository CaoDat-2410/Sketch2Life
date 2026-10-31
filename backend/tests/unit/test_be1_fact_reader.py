from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from sketch2life.domain.eligibility import (
    BASIS_VERSION,
    PROOF_VERSION,
    EligibilityScope,
    ProvisionalDataOrigin,
)
from sketch2life.domain.vision_analysis import ProviderContextMode
from sketch2life.infrastructure.assistance import be1_fact_reader
from sketch2life.infrastructure.assistance import context_revision as revision_module
from sketch2life.infrastructure.assistance.be1_fact_reader import (
    BE1FactReader,
    BE1FactRequest,
    BE1FactSnapshot,
    BE1SyntheticProofFact,
    FactReaderReason,
)

revision_digest = revision_module.context_revision


def _context_digest(payload: dict[str, object]) -> str:
    digest = getattr(revision_module, "context_digest", None)
    assert callable(digest), "the full-context SHA-256 digest helper is not implemented"
    return cast(str, digest(payload))


NOW = datetime(2026, 10, 31, 12, tzinfo=UTC)
ORG = "org-1"
CLASS = "class-1"
SESSION = "session-1"
CHILD = "child-1"
PURPOSE = "purpose-1"
SCOPE = EligibilityScope(ORG, CLASS, CHILD, PURPOSE)


class MemorySource:
    def __init__(self, snapshot: BE1FactSnapshot | None) -> None:
        self.snapshot = snapshot

    def current_facts(self, request: BE1FactRequest) -> BE1FactSnapshot | None:
        del request
        return self.snapshot


def _snapshot(**changes: object) -> BE1FactSnapshot:
    proof = BE1SyntheticProofFact(
        evidence_id="proof-1",
        schema_version=PROOF_VERSION,
        data_origin="SYNTHETIC_DEV",
        scope=SCOPE,
        run_ref="run-1",
        session_id=SESSION,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=1),
        revoked_at=None,
        revocation_revision=0,
    )
    values: dict[str, object] = {
        "organization_id": ORG,
        "class_id": CLASS,
        "session_id": SESSION,
        "session_state": "active",
        "session_run_ref": "run-1",
        "environment": "test",
        "pilot_enabled": True,
        "purpose_ref": PURPOSE,
        "child_id": CHILD,
        "profile_origin": ProvisionalDataOrigin.SYNTHETIC_DEV,
        "profile_state": "active",
        "age_months": 60,
        "age_revision": 1,
        "age_source": "SYNTHETIC_FIXTURE",
        "consent_record_ref": None,
        "consent_revision": None,
        "consent_state": None,
        "legal_consent_effective": False,
        "purpose_granted": False,
        "membership_state": "admitted",
        "group_id": "group-1",
        "proof": proof,
        "evaluated_at": NOW,
    }
    values.update(changes)
    return BE1FactSnapshot(**values)  # type: ignore[arg-type]


def _request(
    *,
    audience: tuple[str, ...] = (CHILD,),
    mode: ProviderContextMode = ProviderContextMode.IMAGE_ONLY,
) -> BE1FactRequest:
    return BE1FactRequest(
        organization_id=ORG,
        class_id=CLASS,
        session_id=SESSION,
        child_id=CHILD,
        purpose_ref=PURPOSE,
        audience_participant_ids=audience,
        context_mode=mode,
    )


def _read(snapshot: BE1FactSnapshot | None, request: BE1FactRequest | None = None):
    return BE1FactReader(MemorySource(snapshot)).read(request or _request())


def test_valid_synthetic_snapshot_returns_consistent_be2_facts() -> None:
    result = _read(_snapshot())
    assert result.reason is FactReaderReason.ALLOWED
    assert result.member is not None and result.context is not None
    assert result.member.consent_record_ref is None
    assert result.member.consent_revision is None
    assert result.member.consent_effective is False
    assert result.member.purpose_granted is False
    assert result.member.age_revision == 1
    assert result.member.age_provenance_ref == "be1-profile-age-v2:SYNTHETIC_FIXTURE:1"
    assert result.member.eligibility_basis == "SYNTHETIC_DEV"
    assert result.member.basis_version == BASIS_VERSION
    assert result.member.evidence_ref == "proof-1"
    assert result.context.context_revision == result.context_revision
    assert result.context.context_digest is not None
    assert result.context.context_digest.startswith("sha256:")
    assert result.context.session_active is True
    assert result.context.audience_age_months == ((CHILD, 60),)
    assert result.context.eligibility_scope == SCOPE


@pytest.mark.parametrize(
    ("changes", "reason"),
    (
        (
            {"profile_origin": ProvisionalDataOrigin.LEGACY_UNCLASSIFIED},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        (
            {"profile_origin": ProvisionalDataOrigin.REAL, "legal_consent_effective": True},
            FactReaderReason.LEGAL_BASIS_DEFERRED,
        ),
        (
            {"profile_origin": ProvisionalDataOrigin.REAL, "legal_consent_effective": False},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        (
            {"profile_origin": ProvisionalDataOrigin.REAL, "legal_consent_effective": None},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        (
            {"profile_origin": ProvisionalDataOrigin.REAL, "consent_state": "pending"},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        (
            {"profile_origin": ProvisionalDataOrigin.REAL, "consent_state": "revoked"},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        ({"profile_state": "archived"}, FactReaderReason.PROFILE_INACTIVE),
        ({"session_state": "paused"}, FactReaderReason.SESSION_NOT_ACTIVE),
        ({"session_state": "finished"}, FactReaderReason.SESSION_NOT_ACTIVE),
        ({"membership_state": "join_pending"}, FactReaderReason.MEMBERSHIP_NOT_ADMITTED),
        ({"group_id": None}, FactReaderReason.MEMBERSHIP_NOT_ADMITTED),
        ({"purpose_ref": "other"}, FactReaderReason.SCOPE_MISMATCH),
        ({"environment": "production"}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"pilot_enabled": False}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"age_months": None}, FactReaderReason.FACTS_INVALID),
        ({"age_revision": 0}, FactReaderReason.FACTS_INVALID),
        ({"age_source": "UNRECOGNIZED"}, FactReaderReason.FACTS_INVALID),
        ({"consent_record_ref": "synthetic-consent"}, FactReaderReason.FACTS_INVALID),
        ({"consent_revision": 1}, FactReaderReason.FACTS_INVALID),
        ({"consent_state": "pending"}, FactReaderReason.FACTS_INVALID),
    ),
)
def test_reader_fails_closed_for_profile_session_and_member_fact_errors(
    changes: dict[str, object], reason: FactReaderReason
) -> None:
    result = _read(_snapshot(**changes))
    assert result.reason is reason
    assert result.member is None and result.context is None


@pytest.mark.parametrize(
    ("proof_changes", "reason"),
    (
        ({"expires_at": NOW}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"issued_at": NOW + timedelta(minutes=1)}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"revoked_at": NOW, "revocation_revision": 1}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"revoked_at": NOW, "revocation_revision": 0}, FactReaderReason.FACTS_INVALID),
        ({"session_id": "other-session"}, FactReaderReason.ELIGIBILITY_DENIED),
        ({"run_ref": "other-run"}, FactReaderReason.ELIGIBILITY_DENIED),
        (
            {"scope": EligibilityScope(ORG, CLASS, "other-child", PURPOSE)},
            FactReaderReason.ELIGIBILITY_DENIED,
        ),
        ({"schema_version": "unknown"}, FactReaderReason.ELIGIBILITY_DENIED),
    ),
)
def test_reader_fails_closed_for_synthetic_proof_errors(
    proof_changes: dict[str, object], reason: FactReaderReason
) -> None:
    base = _snapshot()
    assert base.proof is not None
    result = _read(replace(base, proof=replace(base.proof, **proof_changes)))
    assert result.reason is reason


def test_reader_rejects_wrong_request_scope_audience_and_provider_mode() -> None:
    valid = _snapshot()
    mismatched = _read(valid, replace(_request(), class_id="other-class"))
    assert mismatched.reason is FactReaderReason.SCOPE_MISMATCH

    for audience in ((), (CHILD, CHILD), (CHILD, "child-2")):
        result = _read(valid, _request(audience=audience))
        assert result.reason is FactReaderReason.AUDIENCE_UNSUPPORTED

    typed = _read(valid, _request(mode=ProviderContextMode.TYPED_CONTEXT))
    assert typed.reason is FactReaderReason.CONTEXT_MODE_UNSUPPORTED


def test_reader_denies_missing_source_facts() -> None:
    result = _read(None)
    assert result.reason is FactReaderReason.SOURCE_UNAVAILABLE
    assert result.member is None and result.context is None


def test_reader_denies_a_proof_that_is_not_bound_to_a_session() -> None:
    base = _snapshot()
    assert base.proof is not None

    result = _read(replace(base, proof=replace(base.proof, session_id=None)))

    assert result.reason is FactReaderReason.ELIGIBILITY_DENIED
    assert result.member is None and result.context is None
    assert result.context_revision is None


class _FailingSource:
    def __init__(self, error: BaseException) -> None:
        self.error = error
        self.calls = 0

    def current_facts(self, request: BE1FactRequest) -> BE1FactSnapshot | None:
        del request
        self.calls += 1
        raise self.error


@pytest.mark.parametrize(
    "error",
    (
        RuntimeError("postgresql://reader:hunter2@db.internal/be1"),
        TimeoutError("connection to db.internal timed out"),
        ConnectionError("password authentication failed for user reader"),
        ValueError("row 17 has an unexpected shape"),
    ),
    ids=("runtime", "timeout", "connection", "value"),
)
def test_reader_fails_closed_without_leaking_source_errors(error: Exception) -> None:
    source = _FailingSource(error)

    result = BE1FactReader(source).read(_request())

    assert source.calls == 1
    assert result.reason is FactReaderReason.SOURCE_UNAVAILABLE
    assert result.member is None and result.context is None
    assert result.context_revision is None
    rendered = repr(result) + str(result.reason)
    assert str(error) not in rendered
    assert "hunter2" not in rendered and "db.internal" not in rendered


def test_reader_does_not_swallow_process_level_interrupts() -> None:
    with pytest.raises(KeyboardInterrupt):
        BE1FactReader(_FailingSource(KeyboardInterrupt())).read(_request())


def test_reader_denies_a_naive_evaluation_time_instead_of_assuming_utc() -> None:
    naive = NOW.replace(tzinfo=None)

    result = _read(replace(_snapshot(), evaluated_at=naive))

    assert result.reason is FactReaderReason.ELIGIBILITY_DENIED
    assert result.member is None and result.context is None


@pytest.mark.parametrize("field", ("issued_at", "expires_at"))
def test_reader_denies_naive_proof_timestamps(field: str) -> None:
    base = _snapshot()
    assert base.proof is not None
    naive = getattr(base.proof, field).replace(tzinfo=None)

    result = _read(replace(base, proof=replace(base.proof, **{field: naive})))

    assert result.reason is FactReaderReason.ELIGIBILITY_DENIED
    assert result.member is None and result.context is None


def _allowed_revision(snapshot: BE1FactSnapshot) -> int:
    result = _read(snapshot)
    assert result.reason is FactReaderReason.ALLOWED
    assert result.context_revision is not None
    assert result.context is not None
    assert result.context.context_revision == result.context_revision
    revision: int = result.context_revision
    return revision


def _allowed_context_digest(snapshot: BE1FactSnapshot) -> str:
    result = _read(snapshot)
    assert result.reason is FactReaderReason.ALLOWED
    assert result.context is not None
    assert result.context.context_digest is not None
    return cast(str, result.context.context_digest)


def test_context_revision_is_stable_for_identical_facts_and_evaluation_time_changes() -> None:
    base = _snapshot()

    assert _allowed_revision(base) == _allowed_revision(_snapshot())
    assert _allowed_context_digest(base) == _allowed_context_digest(_snapshot())
    assert _allowed_revision(replace(base, evaluated_at=NOW + timedelta(seconds=5))) == (
        _allowed_revision(base)
    )
    assert _allowed_context_digest(replace(base, evaluated_at=NOW + timedelta(seconds=5))) == (
        _allowed_context_digest(base)
    )


def test_context_revision_changes_when_the_proof_evidence_id_changes() -> None:
    base = _snapshot()
    assert base.proof is not None
    changed = replace(base, proof=replace(base.proof, evidence_id="proof-2"))

    assert _allowed_revision(changed) != _allowed_revision(base)
    assert _allowed_context_digest(changed) != _allowed_context_digest(base)
    result = _read(changed)
    assert result.member is not None and result.member.evidence_ref == "proof-2"


@pytest.mark.parametrize(
    "changes",
    (
        {"membership_state": "pending"},
        {"session_state": "paused"},
        {"pilot_enabled": False},
    ),
    ids=("membership", "session-state", "pilot-flag"),
)
def test_context_digest_tracks_membership_session_and_pilot_inputs(
    changes: dict[str, object],
) -> None:
    base = _snapshot()
    changed = replace(base, **changes)  # type: ignore[arg-type]

    digest_before = _context_digest(be1_fact_reader._context_payload(base, BASIS_VERSION))
    digest_after = _context_digest(be1_fact_reader._context_payload(changed, BASIS_VERSION))

    assert digest_before != digest_after


@pytest.mark.parametrize(
    "changes",
    ({"age_revision": 2}, {"age_source": "ADULT_DECLARED"}),
)
def test_context_revision_tracks_persisted_age_provenance(changes: dict[str, object]) -> None:
    base = _snapshot()
    changed = replace(base, **changes)  # type: ignore[arg-type]
    base_payload = be1_fact_reader._context_payload(base, BASIS_VERSION)
    changed_payload = be1_fact_reader._context_payload(changed, BASIS_VERSION)
    assert _context_digest(changed_payload) != _context_digest(base_payload)
    if changes.get("age_revision") is not None:
        assert _allowed_revision(changed) != _allowed_revision(base)
        assert _allowed_context_digest(changed) != _allowed_context_digest(base)


@pytest.mark.parametrize("changes", ({"age_months": 61}, {"group_id": "group-2"}))
def test_context_revision_tracks_other_fenced_facts(changes: dict[str, object]) -> None:
    base = _snapshot()

    assert _allowed_revision(replace(base, **changes)) != _allowed_revision(base)  # type: ignore[arg-type]
    assert _allowed_context_digest(replace(base, **changes)) != _allowed_context_digest(base)  # type: ignore[arg-type]


def test_revocation_revision_is_fenced_but_unreachable_through_an_allowed_read() -> None:
    base = _snapshot()
    assert base.proof is not None
    revoked = replace(
        base,
        proof=replace(base.proof, revoked_at=NOW - timedelta(seconds=1), revocation_revision=1),
    )
    # Through the reader a revoked proof is refused before any digest exists...
    assert _read(revoked).reason is FactReaderReason.ELIGIBILITY_DENIED

    # ...so the payload is checked directly: a bumped revocation revision moves the digest.
    payload_before = be1_fact_reader._context_payload(base, BASIS_VERSION)
    payload_after = be1_fact_reader._context_payload(revoked, BASIS_VERSION)
    assert payload_before["proof_revocation_revision"] == 0
    assert payload_after["proof_revocation_revision"] == 1
    digest_before = revision_digest(payload_before)
    digest_after = revision_digest(payload_after)
    assert digest_before != digest_after

    assert revoked.proof is not None
    bumped = replace(revoked, proof=replace(revoked.proof, revocation_revision=2))
    digest_bumped = revision_digest(be1_fact_reader._context_payload(bumped, BASIS_VERSION))
    assert digest_bumped != digest_after
