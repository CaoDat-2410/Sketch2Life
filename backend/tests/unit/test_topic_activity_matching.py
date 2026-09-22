from __future__ import annotations

from pathlib import Path

from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.semantic_activity_resolver import (
    resolve_activity_options,
)
from sketch2life.application.services.topic_semantics import (
    RankedClaim,
    compose_topic_vi,
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
    assert compose_topic_vi(claims) == "Con bướm đang bay trong thiên nhiên"


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
