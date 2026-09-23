from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.semantic_activity_resolver import (
    resolve_activity_options,
    resolve_activity_options_v2,
)
from sketch2life.application.services.topic_semantics import (
    RankedClaim,
    build_topic_directions,
    compose_topic_vi,
    display_label_vi,
    rank_claims,
)
from sketch2life.contracts.schemas.p1_experience import (
    AnchorProvenanceV1,
    SemanticAnchorSetV1,
    SemanticAnchorV1,
)
from sketch2life.infrastructure.catalog.activity_semantics import (
    load_activity_semantic_catalog,
)
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library

ROOT = Path(__file__).resolve().parents[3]


def _anchor(label: str, *, tags: tuple[str, ...] = ()) -> SemanticAnchorSetV1:
    digest = "a" * 64
    return SemanticAnchorSetV1(
        anchor_set_id="anchors-test",
        source_artifact_id="drawing.png",
        source_artifact_sha256=digest,
        gate_a_status="CONFIRMED",
        adult_confirmation_actor="PROJECT_OWNER",
        primary_anchor=SemanticAnchorV1(
            anchor_id="anchor-subject-1",
            kind="subject",
            original_label=label,
            normalized_label=label,
            semantic_tags=tags,
            confidence=0.96,
            adult_confirmed=True,
            provenance=AnchorProvenanceV1(
                source_artifact_id="drawing.png",
                source_artifact_sha256=digest,
                source_contract_name="RawUnderstandingResultV1",
                source_contract_version="1.0",
                source_claim_ids=("subject-1",),
            ),
        ),
    )


def test_claim_ranking_demotes_background_and_composes_grounded_topic() -> None:
    claims = rank_claims(
        (
            RankedClaim("theme-1", "nature", "thiên nhiên", "story", 0.99),
            RankedClaim("subject-1", "butterfly", "con bướm", "subject", 0.88),
            RankedClaim("action-1", "flying", "bay", "action", 0.95),
        )
    )

    assert claims[0].observation_id == "subject-1"
    assert compose_topic_vi(claims) == "Cùng khám phá con bướm đang bay giữa thiên nhiên!"


def test_bird_claims_are_localized_deduplicated_and_compose_one_vietnamese_topic() -> None:
    claims = rank_claims(
        (
            RankedClaim("subject-bird", "bird", display_label_vi("bird"), "subject", 0.96),
            RankedClaim("subject-branch", "branch", display_label_vi("branch"), "subject", 0.91),
            RankedClaim("subject-leaf", "leaf", display_label_vi("leaf"), "subject", 0.88),
            RankedClaim("subject-leaves", "leaves", display_label_vi("leaves"), "subject", 0.86),
            RankedClaim(
                "action-perching",
                "perching",
                display_label_vi("perching"),
                "action",
                0.95,
            ),
            RankedClaim(
                "story-bird",
                "bird on branch",
                display_label_vi("bird on branch"),
                "story",
                0.93,
            ),
        )
    )

    assert [claim.observation_id for claim in claims].count("subject-leaf") == 1
    assert "subject-leaves" not in {claim.observation_id for claim in claims}
    assert not {
        "bird",
        "branch",
        "leaf",
        "leaves",
        "perching",
        "bird on branch",
    }.intersection({claim.display_label for claim in claims})
    assert compose_topic_vi(claims) == "Cùng khám phá con chim đậu trên cành cây!"

    directions = build_topic_directions(claims, narration_available=True)
    assert 1 <= len(directions) <= 3
    assert directions[0].title_vi == "Cùng khám phá con chim đậu trên cành cây!"
    assert directions[0].source_claim_ids == (
        "subject-bird",
        "action-perching",
        "story-bird",
    )
    assert directions[0].narration_covered is True
    assert all("chi tiết trong tranh" not in item.title_vi for item in directions)
    assert len({item.title_vi for item in directions}) == len(directions)


def test_v2_bird_shortlist_is_bounded_and_never_uses_unrelated_transfer() -> None:
    library = load_p1_template_library(ROOT, include_mvp=True, include_expansion=True)
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)

    recommendation = resolve_activity_options_v2(
        anchor_set=_anchor("con chim đậu trên cành", tags=("động vật", "chuyển động")),
        age_months=60,
        catalog=load_activity_semantic_catalog_v2(ROOT, include_expansion=True),
        compiler=compiler,
        narration_text="Con chim đang đậu trên cành cây.",
    )

    activity_ids = tuple(option.activity_ref.id for option in recommendation.options)
    assert 1 <= len(activity_ids) <= 3
    assert activity_ids == ("ACT-0102", "ACT-0106", "ACT-0110")
    assert "ACT-0026" not in activity_ids
    assert all(recommendation.v2_match_for(activity_id) for activity_id in activity_ids)


def test_semantic_catalog_returns_safe_age_fallback_for_raw_english_background() -> None:
    library = load_p1_template_library(ROOT, include_mvp=True)
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
    catalog = load_activity_semantic_catalog(ROOT)

    recommendation = resolve_activity_options(
        anchor_set=_anchor("grass", tags=("thiên nhiên", "quan sát cây")),
        age_months=60,
        catalog=catalog,
        compiler=compiler,
    )

    assert recommendation.options
    assert recommendation.options[0].activity_ref.id == "ACT-0026"
    assert recommendation.selected_evidence is not None
    assert recommendation.selected_evidence.match_mode == "SAFE_FALLBACK"
    assert recommendation.metadata()["status"] == "EXPANDED"


def test_semantic_tag_can_reach_reviewed_concept_family_when_age_allows_it() -> None:
    library = load_p1_template_library(ROOT, include_mvp=True)
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
    catalog = load_activity_semantic_catalog(ROOT)

    recommendation = resolve_activity_options(
        anchor_set=_anchor("grass", tags=("quan sát cây",)),
        age_months=72,
        catalog=catalog,
        compiler=compiler,
    )

    assert recommendation.options
    assert recommendation.options[0].activity_ref.id == "ACT-0055"
    assert recommendation.selected_evidence is not None
    assert recommendation.selected_evidence.match_mode == "ALIAS"
    assert "REVIEWED_CONCEPT_FAMILY" in recommendation.selected_evidence.reason_codes


def test_butterfly_token_overlap_never_exposes_unrelated_clamp_activity() -> None:
    library = load_p1_template_library(ROOT, include_mvp=True)
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
    anchor = _anchor("butterfly", tags=("động vật", "chuyển động"))

    direct = compiler.context_options(anchor, age_months=60)
    recommendation = resolve_activity_options(
        anchor_set=anchor,
        age_months=60,
        catalog=load_activity_semantic_catalog(ROOT),
        compiler=compiler,
    )

    assert all(option.activity_ref.id != "ACT-0029" for option in direct)
    assert recommendation.options
    assert recommendation.options[0].activity_ref.id == "ACT-0026"
    assert recommendation.selected_evidence is not None
    assert recommendation.selected_evidence.match_mode == "SAFE_FALLBACK"


def test_resolver_continues_to_reviewed_fallback_after_first_fit_rejection(
    monkeypatch,
) -> None:
    library = load_p1_template_library(ROOT, include_mvp=True)
    compiler = P1ExperienceCompiler(library.templates, library.objective_titles_vi)
    catalog = load_activity_semantic_catalog(ROOT)
    exact_profile = catalog.profile_for("ACT-0029")
    fallback_profile = catalog.profile_for("ACT-0026")

    class _TwoCandidateCatalog:
        profiles = (exact_profile, fallback_profile)

        @staticmethod
        def match(anchor_set, profile):
            return catalog.match(anchor_set, profile)

    original_candidate_fit = compiler.candidate_fit

    def _candidate_fit(anchor_set, *, template_id, semantic_match=None):
        if template_id == compiler.template_id_for_activity_id("ACT-0029"):
            return SimpleNamespace(status="REJECT", reason_codes=("FIT_BELOW_THRESHOLD",))
        return original_candidate_fit(
            anchor_set,
            template_id=template_id,
            semantic_match=semantic_match,
        )

    monkeypatch.setattr(compiler, "candidate_fit", _candidate_fit)
    recommendation = resolve_activity_options(
        anchor_set=_anchor("chuyển vật bằng kẹp"),
        age_months=60,
        catalog=_TwoCandidateCatalog(),
        compiler=compiler,
    )

    assert recommendation.options[0].activity_ref.id == "ACT-0026"
    assert recommendation.selected_evidence is not None
    assert recommendation.selected_evidence.match_mode == "SAFE_FALLBACK"
    assert recommendation.rejected_reason_codes == ("FIT_BELOW_THRESHOLD",)
