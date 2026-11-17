"""BE2-02 C2 typed-context domain rules: snapshot gate, projection, digests (C2-A01/A02/A03/
A04/A12). Synthetic fixture facts only; the band policy is FIXTURE_ONLY, not adopted."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sketch2life.domain.vision_analysis import TypedContextBinding
from sketch2life.domain.vision_context import (
    FIXTURE_AGE_BAND_POLICY,
    PROVIDER_CONTEXT_FIELDS,
    AgeBand,
    AgeBandPolicy,
    ContextCode,
    ContextPortFacts,
    ContextRuleViolation,
    MemberContextFact,
    ProviderContextProjection,
    RequestContextFact,
    RequestedLevel,
    RequestReason,
    TargetKind,
    TeacherTopicFact,
    VisionContextSnapshot,
    context_digest,
    payload_digest,
    pin_context,
    project_provider_context,
    strict_canonical_sha256,
    verify_context_snapshot,
)
from sketch2life.infrastructure.vision_analysis.harness import (
    CHILD_A,
    CHILD_B,
    AnalysisHarness,
    build_analysis_harness,
)


def _group() -> AnalysisHarness:
    h = build_analysis_harness()
    h.pin = replace(h.pin, scope=replace(h.pin.scope, group_id="group_fx_1",
                                         audience_participant_ids=(CHILD_A, CHILD_B)))
    h.requests.add(h.pin)
    h.set_job()
    return h


def _snapshot(h: AnalysisHarness) -> VisionContextSnapshot:
    snapshot = h.context_sources.resolve(h.pin, h.snapshot)
    assert snapshot is not None
    return snapshot


def _port(h: AnalysisHarness) -> ContextPortFacts:
    decision = h.context.current(h.pin.scope)
    return ContextPortFacts(decision.context_revision, decision.consent_effective,
                            decision.purpose_granted, decision.session_active,
                            decision.audience_age_months)


def _verify(h: AnalysisHarness, snapshot: VisionContextSnapshot,
            port: ContextPortFacts | None = None) -> ContextCode | None:
    return verify_context_snapshot(
        snapshot, pin=h.pin, source=h.snapshot, policy=FIXTURE_AGE_BAND_POLICY,
        port=port or _port(h), expected_context_revision=h.pin.context_revision,
    )


def _member(**changes: object) -> MemberContextFact:
    base = MemberContextFact(
        participant_id="participant_fx_a", completed_age_months=60,
        age_provenance_ref="profile-age:participant_fx_a", age_revision=1,
        consent_effective=True, consent_record_ref="consent-record:participant_fx_a",
        purpose_granted=True, provider_transfer_permitted=True,
        permitted_fields=frozenset(PROVIDER_CONTEXT_FIELDS), permission_revision=1,
    )
    return replace(base, **changes)  # type: ignore[arg-type]


# ---------------------------------------------------------------- C2-A01 strict facts
@pytest.mark.parametrize(
    "changes",
    [
        {"completed_age_months": True},
        {"completed_age_months": "60"},
        {"completed_age_months": 60.0},
        {"completed_age_months": -1},
        {"participant_id": ""},
        {"participant_id": "participant_fx_a\n"},
        {"participant_id": "participant fx"},
        {"consent_record_ref": "consent\x00record"},
        {"consent_effective": 1},
        {"provider_transfer_permitted": "yes"},
        {"permitted_fields": frozenset({"child_explanation"})},
        {"permitted_fields": {"teacher_topic"}},
        {"age_revision": 0},
        {"permission_revision": True},
    ],
)
def test_c2_a01_member_facts_reject_coercion_bypasses(changes: dict[str, object]) -> None:
    with pytest.raises(ContextRuleViolation):
        _member(**changes)


def test_c2_a01_topic_and_request_facts_are_bounded_and_teacher_authored() -> None:
    TeacherTopicFact("topic_fx_1", 1, "Animals", "teacher", "teacher_fx_001")
    for bad in (
        {"text": " Animals"},           # not normalized
        {"text": ""},
        {"text": "A" * 129},
        {"text": "Ani\x07mals"},
        {"author_role": "child_device"},  # never a Child statement
        {"topic_ref": "topic\n"},
        {"topic_revision": False},
    ):
        with pytest.raises(ContextRuleViolation):
            replace(TeacherTopicFact("topic_fx_1", 1, "Animals", "teacher", "teacher_fx_001"),
                    **bad)
    with pytest.raises(ContextRuleViolation):
        RequestContextFact("describe_drawing", TargetKind.WHOLE_CANVAS,  # type: ignore[arg-type]
                           RequestedLevel.BRIEF)


def test_c2_a01_snapshot_and_binding_reject_malformed_values() -> None:
    h = build_analysis_harness()
    snapshot = _snapshot(h)
    for bad in ({"group_id": ""}, {"render_sha256": "A" * 64}, {"context_revision": True},
                {"audience_participant_ids": ()}, {"audience_participant_ids": ["p"]},
                {"session_active": 0}, {"request_revision": 0},
                {"members": [_member()]}):
        with pytest.raises(ContextRuleViolation):
            replace(snapshot, **bad)
    binding = pin_context(snapshot, FIXTURE_AGE_BAND_POLICY).binding
    with pytest.raises(ValueError):
        replace(binding, context_digest=binding.payload_digest)
    with pytest.raises(ValueError):
        replace(binding, context_revision=True)
    with pytest.raises(ValueError):
        TypedContextBinding(binding.context_contract, binding.context_contract_version,
                            binding.canonical_rules_version, 3, "a" * 64, "b" * 63,
                            "fixture-completed-years-v1", "1")


# ------------------------------------------------------------- C2-A02 coherent binding
def test_c2_a02_fixture_snapshot_is_coherent_with_the_pin_source_and_old_port() -> None:
    h = _group()
    assert _verify(h, _snapshot(h)) is None


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"organization_id": "org_fx_school_b"}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"class_id": "class_fx_b"}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"session_id": "session_fx_002"}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"canvas_id": "canvas_fx_002"}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"group_id": None}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"contributor_participant_id": CHILD_B}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"purpose_code": "other_purpose"}, ContextCode.CONTEXT_SCOPE_MISMATCH),
        ({"assistance_id": "assistance_fx_002"}, ContextCode.CONTEXT_REQUEST_MISMATCH),
        ({"request_revision": 2}, ContextCode.CONTEXT_REQUEST_MISMATCH),
        ({"render_sha256": "f" * 64}, ContextCode.CONTEXT_SOURCE_MISMATCH),
        ({"checkpoint_checksum": "e" * 64}, ContextCode.CONTEXT_SOURCE_MISMATCH),
        ({"age_band_policy_version": "2"}, ContextCode.CONTEXT_POLICY_MISMATCH),
        ({"canonical_rules_version": "vision-context-canonical-v0"},
         ContextCode.CONTEXT_POLICY_MISMATCH),
        ({"context_revision": 4}, ContextCode.CONTEXT_REVISION_MISMATCH),
        ({"session_active": False}, ContextCode.INVALID_STATE),
    ],
)
def test_c2_a02_wrong_scope_request_source_policy_or_revision_refuses(
    changes: dict[str, object], code: ContextCode
) -> None:
    h = _group()
    assert _verify(h, replace(_snapshot(h), **changes)) is code  # type: ignore[arg-type]


def test_c2_a02_missing_extra_and_duplicate_audience_refuse_before_conversion() -> None:
    h = _group()
    snapshot = _snapshot(h)
    a, b = snapshot.members
    missing = replace(snapshot, audience_participant_ids=(CHILD_A,), members=(a,))
    assert _verify(h, missing) is ContextCode.CONTEXT_AUDIENCE_MISMATCH
    extra_member = replace(a, participant_id="participant_fx_z")
    extra = replace(snapshot, audience_participant_ids=(CHILD_A, CHILD_B, "participant_fx_z"),
                    members=(a, b, extra_member))
    assert _verify(h, extra) is ContextCode.CONTEXT_AUDIENCE_MISMATCH
    # A duplicate whose second copy would win a dict conversion is refused first.
    shadow = replace(b, completed_age_months=200)
    duplicate = replace(snapshot, members=(a, b, shadow))
    assert _verify(h, duplicate) is ContextCode.CONTEXT_AUDIENCE_DUPLICATE
    dup_audience = replace(snapshot, audience_participant_ids=(CHILD_A, CHILD_B, CHILD_B))
    assert _verify(h, dup_audience) is ContextCode.CONTEXT_AUDIENCE_DUPLICATE
    port = _port(h)
    dup_port = replace(port, audience_age_months=(*port.audience_age_months, (CHILD_B, 200)))
    assert _verify(h, snapshot, dup_port) is ContextCode.CONTEXT_AUDIENCE_DUPLICATE
    with pytest.raises(ContextRuleViolation):
        context_digest(duplicate, "a" * 64)


@pytest.mark.parametrize(
    "port_change",
    [
        {"context_revision": 4},
        {"session_active": False},
        {"consent_effective": False},
        {"purpose_granted": False},
        {"audience_age_months": ((CHILD_A, 60), (CHILD_B, 121))},
        {"audience_age_months": ((CHILD_A, 60),)},
    ],
)
def test_c2_a02_disagreeing_old_and_new_context_ports_refuse(
    port_change: dict[str, object]
) -> None:
    h = _group()
    port = replace(_port(h), **port_change)  # type: ignore[arg-type]
    assert _verify(h, _snapshot(h), port) is ContextCode.CONTEXT_PORT_DISAGREEMENT


# --------------------------------------------------------- C2-A03 per-member eligibility
@pytest.mark.parametrize(
    ("member_change", "code"),
    [
        ({"completed_age_months": None}, ContextCode.AGE_NOT_SUPPORTED),
        ({"completed_age_months": 35}, ContextCode.AGE_NOT_SUPPORTED),
        ({"completed_age_months": 156}, ContextCode.AGE_NOT_SUPPORTED),
        ({"consent_effective": False}, ContextCode.CONSENT_REQUIRED),
        ({"purpose_granted": False}, ContextCode.CONSENT_REQUIRED),
        ({"provider_transfer_permitted": False}, ContextCode.TRANSFER_NOT_PERMITTED),
        ({"permitted_fields": frozenset({"audience_age_bands", "request_enums"})},
         ContextCode.CONTEXT_FIELD_NOT_PERMITTED),
    ],
)
def test_c2_a03_a04_one_member_failing_refuses_the_whole_context(
    member_change: dict[str, object], code: ContextCode
) -> None:
    h = _group()
    snapshot = _snapshot(h)
    a, b = snapshot.members
    bad = replace(snapshot, members=(a, replace(b, **member_change)))  # type: ignore[arg-type]
    assert _verify(h, bad) is code


def test_c2_a03_fixture_bands_cover_36_to_155_exactly_once() -> None:
    policy = FIXTURE_AGE_BAND_POLICY
    assert policy.status == "FIXTURE_ONLY_NOT_PEDAGOGICALLY_ADOPTED"
    assert len(policy.bands) == 10
    assert [(b.min_months, b.max_months) for b in policy.bands][0] == (36, 47)
    assert [(b.min_months, b.max_months) for b in policy.bands][-1] == (144, 155)
    for months in range(36, 156):
        assert sum(b.min_months <= months <= b.max_months for b in policy.bands) == 1
    assert policy.band_for(36) == policy.band_for(47) == "completed-years-3"
    assert policy.band_for(48) == "completed-years-4"
    assert policy.band_for(155) == "completed-years-12"
    for outside in (35, 156):
        with pytest.raises(ContextRuleViolation):
            policy.band_for(outside)
    with pytest.raises(ContextRuleViolation):
        policy.band_for(True)


@pytest.mark.parametrize(
    "bands",
    [
        (AgeBand("a", 36, 100), AgeBand("b", 100, 155)),   # overlap
        (AgeBand("a", 36, 99), AgeBand("b", 101, 155)),    # gap
        (AgeBand("a", 37, 155),),                          # coverage starts late
        (AgeBand("a", 36, 154),),                          # coverage ends early
        (AgeBand("a", 36, 99), AgeBand("a", 100, 155)),    # duplicate label
        (),
    ],
)
def test_c2_a03_band_policy_rejects_overlap_gaps_and_partial_coverage(
    bands: tuple[AgeBand, ...]
) -> None:
    with pytest.raises(ContextRuleViolation):
        AgeBandPolicy("policy_fx", "1", "FIXTURE_ONLY", bands)


def test_c2_a03_projection_is_per_member_sorted_bands_without_identity_or_mean() -> None:
    h = _group()
    snapshot = _snapshot(h)
    a, b = snapshot.members
    extremes = replace(snapshot, members=(replace(a, completed_age_months=36),
                                          replace(b, completed_age_months=155)))
    projection = project_provider_context(extremes, FIXTURE_AGE_BAND_POLICY)
    # One label per member, canonical (lexicographic) order; no mean (~95 months) band.
    assert projection.audience_age_bands == ("completed-years-12", "completed-years-3")
    same = replace(snapshot, members=(replace(a, completed_age_months=60),
                                      replace(b, completed_age_months=61)))
    assert project_provider_context(same, FIXTURE_AGE_BAND_POLICY).audience_age_bands == (
        "completed-years-5", "completed-years-5")  # duplicates/count kept
    document = projection.canonical()
    text = repr({k: v for k, v in document.items() if k != "source_image_sha256"})
    for internal in (CHILD_A, CHILD_B, "consent-record", "profile-age", "teacher_fx_001",
                     "36", "155", "org_fx", "session_fx", "class_fx"):
        assert internal not in text, internal
    assert set(document) == {
        "contract_name", "contract_version", "context_revision", "teacher_topic",
        "audience_age_bands", "age_band_policy_ref", "age_band_policy_version",
        "request_reason", "target_kind", "requested_level", "source_image_sha256"}


def test_c2_a04_absent_topic_is_null_never_empty() -> None:
    h = build_analysis_harness()
    h.context_sources.topic = None
    projection = project_provider_context(_snapshot(h), FIXTURE_AGE_BAND_POLICY)
    assert projection.canonical()["teacher_topic"] is None
    with pytest.raises(ValueError):
        replace(projection, teacher_topic="")
    with pytest.raises(ContextRuleViolation):
        replace(projection, audience_age_bands=("completed-years-5", "completed-years-3"))


# ------------------------------------------------------------------- C2-A12 digests
def _digests(snapshot: VisionContextSnapshot) -> tuple[str, str]:
    binding = pin_context(snapshot, FIXTURE_AGE_BAND_POLICY).binding
    return binding.payload_digest, binding.context_digest


def test_c2_a12_digests_are_stable_under_member_and_audience_reorder() -> None:
    h = _group()
    snapshot = _snapshot(h)
    reordered = replace(snapshot, members=tuple(reversed(snapshot.members)),
                        audience_participant_ids=tuple(reversed(
                            snapshot.audience_participant_ids)))
    assert _digests(reordered) == _digests(snapshot)
    fields = replace(snapshot.members[0], permitted_fields=frozenset(
        reversed(PROVIDER_CONTEXT_FIELDS)))
    assert _digests(replace(snapshot, members=(fields, snapshot.members[1]))) == (
        _digests(snapshot))


@pytest.mark.parametrize(
    ("label", "change"),
    [
        ("exact age inside the same band", lambda s: replace(
            s, members=(replace(s.members[0], completed_age_months=61), *s.members[1:]))),
        ("age provenance revision", lambda s: replace(
            s, members=(replace(s.members[0], age_revision=2), *s.members[1:]))),
        ("permission revision", lambda s: replace(
            s, members=(replace(s.members[0], permission_revision=2), *s.members[1:]))),
        ("consent record", lambda s: replace(
            s, members=(replace(s.members[0], consent_record_ref="consent-record:v2"),
                        *s.members[1:]))),
        ("field policy revision", lambda s: replace(s, field_policy_revision=2)),
        ("topic provenance revision", lambda s: replace(
            s, topic=replace(s.topic, topic_revision=2))),
        ("request revision", lambda s: replace(s, request_revision=2)),
        ("source checkpoint", lambda s: replace(s, checkpoint_checksum="e" * 64)),
        ("policy version", lambda s: replace(s, age_band_policy_version="2")),
        ("session", lambda s: replace(s, session_id="session_fx_002")),
    ],
)
def test_c2_a12_internal_movement_changes_context_digest_only_when_projection_stable(
    label: str, change: object
) -> None:
    h = _group()
    snapshot = _snapshot(h)
    moved = change(snapshot)  # type: ignore[operator]
    payload, context = _digests(snapshot)
    moved_payload = payload_digest(project_provider_context(moved, FIXTURE_AGE_BAND_POLICY))
    assert context_digest(moved, moved_payload) != context, label
    if label in {"exact age inside the same band", "age provenance revision",
                 "permission revision", "consent record", "field policy revision",
                 "topic provenance revision", "request revision", "session"}:
        # Internal-only facts never reach the provider projection.
        assert moved_payload == payload, label


def test_c2_a12_projection_changes_move_both_digests() -> None:
    h = _group()
    snapshot = _snapshot(h)
    base = _digests(snapshot)
    for moved in (
        replace(snapshot, request=replace(snapshot.request,
                                          reason=RequestReason.SUPPORT_MEANING_CHECK)),
        replace(snapshot, members=(replace(snapshot.members[0], completed_age_months=72),
                                   snapshot.members[1])),
        replace(snapshot, render_sha256="f" * 64),
        replace(snapshot, topic=None),
    ):
        payload, context = _digests(moved)
        assert payload != base[0] and context != base[1]


def test_c2_a12_payload_digest_is_recomputable_and_has_no_self_or_time_fields() -> None:
    h = build_analysis_harness()
    typed = pin_context(_snapshot(h), FIXTURE_AGE_BAND_POLICY)
    document = typed.projection.canonical()
    assert strict_canonical_sha256(document) == typed.binding.payload_digest
    for forbidden in ("payload_digest", "context_digest", "executed_at", "correlation_id",
                      "recorded_at"):
        assert forbidden not in document
    # Re-pinning later (different clock) yields the identical binding.
    h.clock.advance(seconds=600)
    assert pin_context(_snapshot(h), FIXTURE_AGE_BAND_POLICY).binding == typed.binding


@pytest.mark.parametrize(
    "document",
    [{"x": 1.5}, {"x": float("nan")}, {"x": float("inf")}, {1: "a"}, {"x": object()},
     {"x": {"y": [b"bytes"]}}],
)
def test_c2_a12_strict_canonical_hash_refuses_malformed_values(document: object) -> None:
    with pytest.raises(ContextRuleViolation):
        strict_canonical_sha256(document)  # type: ignore[arg-type]


def test_c2_a12_projection_rejects_unsorted_or_identity_like_bands() -> None:
    with pytest.raises(ContextRuleViolation):
        ProviderContextProjection(3, None, ("Participant_FX_A",), "fixture-completed-years-v1",
                                  "1", RequestReason.DESCRIBE_DRAWING, TargetKind.WHOLE_CANVAS,
                                  RequestedLevel.STANDARD, "a" * 64)
    with pytest.raises(ContextRuleViolation):
        ProviderContextProjection(3, None, (), "fixture-completed-years-v1", "1",
                                  RequestReason.DESCRIBE_DRAWING, TargetKind.WHOLE_CANVAS,
                                  RequestedLevel.STANDARD, "a" * 64)
