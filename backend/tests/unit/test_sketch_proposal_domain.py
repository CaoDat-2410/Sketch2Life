"""BE2-04 SK1.1 domain: SK-P11 (domain), SK-N11, SK-N18, SK-N19, SK-N24a, SK-C03, SK-C03b."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from hashlib import sha256

import pytest

from sketch2life.domain.sketch_proposal import (
    PNG_SIGNATURE,
    AssetRef,
    CurrentFacts,
    DisplayMode,
    InvalidSketchTransition,
    LevelOutputRule,
    LevelSource,
    MeaningBasis,
    ModerationState,
    OutputPart,
    PartRequirement,
    PipelineState,
    ProducerRef,
    PromotedOutput,
    SketchProposal,
    SketchRuleViolation,
    StatusReason,
    content_sha256,
    current_verdict,
    device_status,
    generation_digest,
    link_job,
    mark_analyzing,
    normalize_text,
    open_proposal,
    policy_verdict,
    promote,
    revise_level,
    terminate,
    validate_output,
)
from sketch2life.infrastructure.assistance.harness import FIXTURE_START, LEVEL, LEVEL_2
from sketch2life.infrastructure.sketch_generation.fakes import all_current, fixture_sketch_policy
from sketch2life.infrastructure.sketch_generation.harness import make_binding

POLICY = fixture_sketch_policy()
PRODUCER = ProducerRef("fake-sketch-generator", "fixture-sketch-profile-v0", "fixture-config-v0",
                       "fixture")
DOC = AssetRef("artifact_fx_doc", "d" * 64, "application/json", 321)
ASSET = AssetRef("artifact_fx_png", "e" * 64, "image/png", 64)
# SK-C03 / SK-C03b golden vectors (synthetic fixture inputs; recomputed, never edited by hand).
GOLDEN_V1_DIGEST = "f7dd4d613fa9f631e80aa5f776a6205ce56e05938a721e7c71f0f000ea3cb67b"
GOLDEN_V2_DIGEST = "2d544e3335ca88d886f8749b4123e15fe1671f686f12b294ec2ef40839e226b0"
GOLDEN_V1_CONTENT = "d675d12aa81e0f6f5d087a4fb96bf8eff3d94af4af0ed3b99c433c520b163c27"
GOLDEN_V2_CONTENT = "32960bcb5251aebe1d3763ed5d8410a73bc571536ff70870cab1076d0078e40e"


def opened(level: str = LEVEL, *, proposal_id: str = "sketch_fx_golden",
           now: object = FIXTURE_START) -> SketchProposal:
    return open_proposal(proposal_id=proposal_id, binding=make_binding(level=level),
                         policy=POLICY, now=now, refusal=None)  # type: ignore[arg-type]


def pending(proposal: SketchProposal, *, text: str | None = "Fixture prompt?",
            asset: AssetRef | None = None) -> SketchProposal:
    analyzing = mark_analyzing(link_job(proposal, "job_fx_1", FIXTURE_START), "job_fx_1",
                               FIXTURE_START)
    digest = content_sha256(analyzing, analyzing.current, text=text, asset=asset,
                            producer=PRODUCER)
    return promote(analyzing, PromotedOutput("job_fx_1", "att_fx_1", text, asset, DOC, PRODUCER,
                                             digest), FIXTURE_START)


def revised(proposal: SketchProposal) -> SketchProposal:
    rule = POLICY.rule_for(LEVEL_2)
    assert rule is not None
    return revise_level(pending(proposal), rule=rule, receipt_ref="rcpt_fx_revision",
                        policy=POLICY, now=FIXTURE_START)


def png(body: bytes = b"fixture") -> OutputPart:
    data = PNG_SIGNATURE + body
    return OutputPart("reference_image", body=data, media_type="image/png",
                      reported_sha256=sha256(data).hexdigest())


def text(value: str = "What could the cat hold?") -> OutputPart:
    return OutputPart("text_or_question", text=value)


# ------------------------------------------------------------------ SK-C03 / SK-C03b
def test_c03_generation_digest_golden_vector_and_sensitivity() -> None:
    v1 = opened()
    assert v1.current.generation_digest == GOLDEN_V1_DIGEST
    binding = make_binding()
    rule_2 = POLICY.rule_for(LEVEL_2)
    assert rule_2 is not None
    base = dict(binding=binding, proposal_id="sketch_fx_golden", version=1, rule=rule_2,
                policy_ref=POLICY.ref(), generator_profile_ref=POLICY.generator_profile_ref)
    reference = generation_digest(**base)  # type: ignore[arg-type]
    assert reference != v1.current.generation_digest  # level changes the digest
    assert generation_digest(**{**base, "version": 2}) != reference  # type: ignore[arg-type]
    side = replace(rule_2, display_mode=DisplayMode.SIDE_REFERENCE)
    assert generation_digest(**{**base, "rule": side}) != reference  # type: ignore[arg-type]
    confirmed = replace(binding, meaning=MeaningBasis("confirmed", "corr_fx", ("cat",)))
    assert generation_digest(**{**base, "binding": confirmed}) != reference  # type: ignore[arg-type]


def test_c03_content_sha_golden_vector_sensitivity_and_no_timestamps() -> None:
    v1 = pending(opened())
    promoted = v1.current.promoted
    assert promoted is not None and promoted.content_sha256 == GOLDEN_V1_CONTENT
    later = pending(opened(now=FIXTURE_START + timedelta(hours=3)))
    assert later.current.promoted is not None
    assert later.current.promoted.content_sha256 == GOLDEN_V1_CONTENT  # timestamps excluded
    version = v1.current
    same = content_sha256(v1, version, text="Fixture prompt?", asset=None, producer=PRODUCER)
    assert same == GOLDEN_V1_CONTENT
    assert content_sha256(v1, version, text="Other prompt?", asset=None,
                          producer=PRODUCER) != same
    assert content_sha256(v1, version, text="Fixture prompt?", asset=ASSET,
                          producer=PRODUCER) != same
    overlay = replace(version, rule=replace(version.rule, display_mode=DisplayMode.OVERLAY))
    assert content_sha256(v1, overlay, text="Fixture prompt?", asset=None,
                          producer=PRODUCER) != same
    assert content_sha256(v1, replace(version, version=2), text="Fixture prompt?", asset=None,
                          producer=PRODUCER) != same


def test_c03b_versioned_golden_vectors_recompute_from_history() -> None:
    proposal = revised(opened())
    v1, v2 = proposal.versions
    assert v1.generation_digest == GOLDEN_V1_DIGEST
    assert v2.generation_digest == GOLDEN_V2_DIGEST != GOLDEN_V1_DIGEST
    for stored in proposal.versions:  # recomputation from the kept history
        assert generation_digest(proposal.binding, proposal_id=proposal.proposal_id,
                                 version=stored.version, rule=stored.rule,
                                 policy_ref=POLICY.ref(),
                                 generator_profile_ref=POLICY.generator_profile_ref
                                 ) == stored.generation_digest
    analyzing = mark_analyzing(link_job(proposal, "job_fx_2", FIXTURE_START), "job_fx_2",
                               FIXTURE_START)
    digest = content_sha256(analyzing, analyzing.current, text=None, asset=ASSET,
                            producer=PRODUCER)
    assert digest == GOLDEN_V2_CONTENT != GOLDEN_V1_CONTENT


# ------------------------------------------------------------------ SK-P11 / SK-N24a
def test_p11_revised_version_uses_revised_level_everywhere() -> None:
    proposal = revised(opened())
    v1, v2 = proposal.versions
    assert (v1.level, v1.level_source, v1.level_source_ref) == (LEVEL, LevelSource.REQUEST, None)
    assert v1.pipeline_state is PipelineState.STALE
    assert v1.status_reason is StatusReason.SUPERSEDED_BY_REVISION
    assert (v2.level, v2.level_source, v2.level_source_ref) == (
        LEVEL_2, LevelSource.REVISION, "rcpt_fx_revision")
    assert (v2.rule.display_mode, v2.rule.asset) == (DisplayMode.OVERLAY,
                                                     PartRequirement.REQUIRED)
    assert v2.create_key == f"sketch:{proposal.proposal_id}:2:generate"
    assert proposal.binding.requested_level == LEVEL  # BE2-03 request is unchanged
    assert proposal.review_revision == 2


def test_n24a_version_one_level_equals_requested_level() -> None:
    proposal = opened(LEVEL_2)
    assert proposal.current.level == proposal.binding.requested_level == LEVEL_2
    rule = POLICY.rule_for(LEVEL)
    assert rule is not None
    with pytest.raises(SketchRuleViolation):
        replace(proposal, versions=(replace(proposal.current, level=LEVEL,
                                            rule=rule),))


# ------------------------------------------------------------------ SK-N11 / SK-N18
RENDER_SHA = make_binding().source.render_sha256
RULE_1 = POLICY.rule_for(LEVEL)
RULE_2 = POLICY.rule_for(LEVEL_2)


@pytest.mark.parametrize(("rule_level", "parts"), [
    (LEVEL, ()),  # missing required text
    (LEVEL_2, (text(),)),  # missing required asset
    (LEVEL, (text(), png())),  # forbidden asset present
    (LEVEL, (text("   "),)),  # empty after normalisation
    (LEVEL, (text("x" * 4001),)),  # too long (no silent truncation)
    (LEVEL, (text("bad\x07text"),)),  # control character
    (LEVEL_2, (OutputPart("reference_image", body=PNG_SIGNATURE + b"x",
                          media_type="image/gif"),)),  # media type outside allowlist
    (LEVEL_2, (OutputPart("reference_image", body=b"GIF89a", media_type="image/png"),)),
    (LEVEL_2, (OutputPart("reference_image", body=PNG_SIGNATURE + b"x", media_type="image/png",
                          reported_sha256="0" * 64),)),  # reported sha mismatch
    (LEVEL_2, (OutputPart("reference_image", body=PNG_SIGNATURE, media_type="image/png",
                          reported_sha256=None),)),  # placeholder replaced below (render twin)
    (LEVEL, (text(), text("second")),),  # duplicated part
    (LEVEL, (text(), OutputPart("canvas_operations", text="draw a line")),),  # SK-N18
    (LEVEL_2, (OutputPart("stroke_patch", text="{}"),)),  # unknown kind
])
def test_n11_malformed_outputs_are_refused(rule_level: str, parts: tuple[OutputPart, ...]) -> None:
    rule = POLICY.rule_for(rule_level)
    assert rule is not None
    render = RENDER_SHA
    if parts and parts[0].body == PNG_SIGNATURE:  # an output identical to the child's render
        render = sha256(PNG_SIGNATURE).hexdigest()
    assert validate_output(parts, rule, POLICY, render_sha256=render) is None


def test_n11_byte_bound_is_enforced() -> None:
    tight = replace(POLICY, asset_max_bytes=16)
    assert RULE_2 is not None
    assert validate_output((png(b"x" * 32),), RULE_2, tight, render_sha256=RENDER_SHA) is None
    assert validate_output((png(b"x"),), RULE_2, tight, render_sha256=RENDER_SHA) is not None


def test_valid_outputs_are_normalised_and_exact() -> None:
    assert RULE_1 is not None and RULE_2 is not None
    ok = validate_output((text("  Café prompt?  "),), RULE_1, POLICY,
                         render_sha256=RENDER_SHA)
    assert ok is not None and ok.text == "Café prompt?" and ok.asset_body is None
    image = validate_output((png(),), RULE_2, POLICY, render_sha256=RENDER_SHA)
    assert image is not None and image.text is None and image.asset_media_type == "image/png"
    both = validate_output((text(), png()), RULE_2, POLICY, render_sha256=RENDER_SHA)
    assert both is not None and both.text is not None
    assert normalize_text("ok", 1) is None


# ------------------------------------------------------------------ SK-N19 / transitions
def test_n19_producer_never_writes_review_owned_values() -> None:
    proposal = opened()
    version = proposal.current
    for state in (PipelineState.APPROVED, PipelineState.REJECTED):
        with pytest.raises(SketchRuleViolation):
            replace(version, pipeline_state=state)
    with pytest.raises(SketchRuleViolation):
        replace(version, moderation_state=ModerationState.PASSED)
    with pytest.raises(SketchRuleViolation):  # reviewable needs promoted content
        replace(version, pipeline_state=PipelineState.PENDING_TEACHER_REVIEW,
                moderation_state=ModerationState.PENDING)


def test_transitions_and_review_revision() -> None:
    proposal = opened()
    with pytest.raises(InvalidSketchTransition):
        promote(proposal, PromotedOutput("job_fx_1", "att", None, None, DOC, PRODUCER, "a" * 64),
                FIXTURE_START)
    linked = link_job(proposal, "job_fx_1", FIXTURE_START)
    assert link_job(linked, "job_fx_1", FIXTURE_START) is linked
    with pytest.raises(InvalidSketchTransition):
        link_job(linked, "job_fx_other", FIXTURE_START)
    stale = terminate(linked, PipelineState.STALE, StatusReason.CONSENT_REVOKED, FIXTURE_START)
    assert (stale.review_revision, stale.record_version) == (2, 3)
    with pytest.raises(InvalidSketchTransition):
        terminate(stale, PipelineState.CANCELLED, StatusReason.CANCELLED_BY_TEACHER,
                  FIXTURE_START)
    blocked = terminate(mark_analyzing(linked, "job_fx_1", FIXTURE_START),
                        PipelineState.BLOCKED_UNSAFE, StatusReason.UNSAFE_CONTENT, FIXTURE_START)
    assert blocked.current.moderation_state is ModerationState.BLOCKED
    with pytest.raises(InvalidSketchTransition):
        rule = POLICY.rule_for(LEVEL_2)
        assert rule is not None
        revise_level(linked, rule=rule, receipt_ref="rcpt_fx", policy=POLICY, now=FIXTURE_START)
    review = pending(proposal)
    assert review.current.moderation_state is ModerationState.PENDING
    assert terminate(review, PipelineState.STALE, StatusReason.ARTIFACT_QUARANTINED,
                     FIXTURE_START).review_revision == 2


def test_currency_verdict_order_and_policy_verdict() -> None:
    binding = make_binding()
    facts = all_current(binding)
    assert current_verdict(binding, facts) is None
    cases: list[tuple[dict[str, object], StatusReason]] = [
        ({"handoff_unchanged": False}, StatusReason.CONTEXT_CHANGED),
        ({"session_active": False}, StatusReason.SESSION_ENDED),
        ({"consent_ok": False}, StatusReason.CONSENT_REVOKED),
        ({"audience_unchanged": False}, StatusReason.AUDIENCE_CHANGED),
        ({"context_revision": 4}, StatusReason.CONTEXT_CHANGED),
        ({"source_input_hash": "f" * 64}, StatusReason.SOURCE_CHANGED),
        ({"analysis_accepted": False}, StatusReason.ANALYSIS_NOT_APPLICABLE),
        ({"meaning": MeaningBasis("not_applicable", None, ())},
         StatusReason.ANALYSIS_NOT_APPLICABLE),
        ({"meaning": MeaningBasis("confirmed", "corr_fx", ("cat",))},
         StatusReason.MEANING_CHANGED),
    ]
    for changes, reason in cases:
        assert current_verdict(binding, replace(facts, **changes)) is reason  # type: ignore[arg-type]
    # A child proposal does not change the projected meaning basis (TC-07).
    assert current_verdict(binding, replace(facts, meaning=MeaningBasis(
        "unconfirmed", None, ("dog",)))) is None
    assert policy_verdict(None, level=LEVEL, purpose_code="ai_drawing_assistance",
                          opening=True) is StatusReason.POLICY_UNRESOLVED
    assert policy_verdict(replace(POLICY, enabled=False), level=LEVEL,
                          purpose_code="ai_drawing_assistance",
                          opening=True) is StatusReason.POLICY_DISABLED
    assert policy_verdict(POLICY, level="level_fx_9", purpose_code="ai_drawing_assistance",
                          opening=True) is StatusReason.LEVEL_NOT_ALLOWED
    assert policy_verdict(POLICY, level="level_fx_9", purpose_code="ai_drawing_assistance",
                          opening=False) is StatusReason.POLICY_CHANGED
    assert policy_verdict(POLICY, level=LEVEL, purpose_code="other",
                          opening=True) is StatusReason.POLICY_UNRESOLVED


def test_device_status_never_implies_content() -> None:
    assert {device_status(s) for s in PipelineState} == {"pending", "unavailable"}
    assert device_status(PipelineState.PENDING_TEACHER_REVIEW) == "pending"
    assert device_status(PipelineState.BLOCKED_UNSAFE) == "unavailable"


def test_rule_shape_guards() -> None:
    with pytest.raises(SketchRuleViolation):
        LevelOutputRule("level_fx_x", DisplayMode.OVERLAY, PartRequirement.FORBIDDEN,
                        PartRequirement.FORBIDDEN)
    assert RULE_2 is not None
    with pytest.raises(SketchRuleViolation):
        replace(POLICY, rules={"level_fx_1": RULE_2})
    assert isinstance(CurrentFacts, type)
