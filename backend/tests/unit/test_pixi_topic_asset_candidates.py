from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from sketch2life.application.services.pixi_topic_asset_candidates import (
    build_topic_asset_candidate_context,
    load_topic_asset_catalog,
    validate_topic_asset_selection,
)
from sketch2life.contracts.schemas.pixi_topic_asset_selection import (
    AdultConfirmedTopicV1,
    TopicAssetDescriptorV1,
)
from sketch2life.infrastructure.ai.pixi_topic_asset_prompt import build_topic_asset_model_input

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = (
    REPO_ROOT
    / "features"
    / "FEAT-028-pixi-topic-asset-library"
    / "assets"
    / "generated"
    / "asset-catalog.v2.json"
)


def _catalog() -> tuple[TopicAssetDescriptorV1, ...]:
    return load_topic_asset_catalog(CATALOG_PATH)


def _approved(asset: TopicAssetDescriptorV1) -> TopicAssetDescriptorV1:
    value = asset.model_dump(mode="json", by_alias=True)
    value["reviewStatus"] = "APPROVED"
    value["runtimeEligible"] = True
    value["provenance"]["licenseStatus"] = "CLEARED"
    return TopicAssetDescriptorV1.model_validate(value)


def _query(*labels: str, gate_a: bool = True, **kwargs: object) -> AdultConfirmedTopicV1:
    return AdultConfirmedTopicV1(
        gateAConfirmed=gate_a,
        topicLabels=labels or ("chủ đề kiểm thử",),
        **kwargs,
    )


def test_pending_catalog_is_never_offered_to_ai() -> None:
    assets = _catalog()
    query = _query("khủng long")

    context = build_topic_asset_candidate_context(query=query, assets=assets)

    assert context.status == "NO_MATCH"
    assert context.miss_reason == "NO_APPROVED_ASSETS"
    assert context.candidates == ()
    assert context.authoring_queue_proposal is not None
    assert context.authoring_queue_proposal.child_media_included is False
    assert context.authoring_queue_proposal.provider_generation_requested is False


def test_vietnamese_alias_builds_bounded_privacy_minimized_context() -> None:
    assets = _catalog()
    pteranodon = _approved(
        next(item for item in assets if item.asset_id.endswith(".pteranodon.v1"))
    )
    context = build_topic_asset_candidate_context(
        query=_query("khủng long bay", maxCandidates=3),
        assets=(pteranodon,),
    )

    assert context.status == "READY"
    assert [candidate.asset_id for candidate in context.candidates] == [pteranodon.asset_id]
    model_input = build_topic_asset_model_input(context)
    user_payload = json.loads(model_input["userJson"])
    assert user_payload["confirmedTopicLabels"] == ["khủng long bay"]
    assert user_payload["confirmedTopicTags"] == []
    candidate = user_payload["candidateAssets"][0]
    assert candidate["label"]["en"] == "Pteranodon"
    assert "broad wings" in candidate["visualDescription"]["en"]
    assert not {"frame", "provenance", "assetFile", "atlasSha256"} & set(candidate)
    assert "image" not in model_input["userJson"].casefold()
    assert "assetFile" not in model_input["userJson"]


def test_candidate_order_is_deterministic_and_respects_top_k() -> None:
    assets = tuple(_approved(item) for item in _catalog() if item.family == "dinosaurs-prehistory")
    query = _query("dinosaur", maxCandidates=3)

    first = build_topic_asset_candidate_context(query=query, assets=assets)
    second = build_topic_asset_candidate_context(query=query, assets=assets)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert len(first.candidates) == 3
    assert len({candidate.asset_id for candidate in first.candidates}) == 3


def test_compositional_confirmed_topics_retrieve_candidates_for_each_part() -> None:
    catalog = _catalog()
    dinosaur = _approved(
        next(item for item in catalog if item.asset_id.endswith(".tyrannosaurus.v1"))
    )
    swing = _approved(
        next(item for item in catalog if item.asset_id.endswith(".playground-swing.v1"))
    )
    context = build_topic_asset_candidate_context(
        query=_query("dinosaur", "playground"),
        assets=(dinosaur, swing),
    )

    assert {candidate.asset_id for candidate in context.candidates} == {
        dinosaur.asset_id,
        swing.asset_id,
    }


def test_confusable_cues_are_available_to_the_ranker() -> None:
    whale = _approved(next(item for item in _catalog() if item.asset_id.endswith(".whale.v1")))
    context = build_topic_asset_candidate_context(query=_query("cá voi"), assets=(whale,))

    assert context.candidates[0].confusable_with == ("shark", "dolphin")
    model_input = build_topic_asset_model_input(context)
    candidate = json.loads(model_input["userJson"])["candidateAssets"][0]
    assert candidate["confusableWith"] == ["shark", "dolphin"]


def test_full_catalog_has_stable_ids_and_no_unreviewed_runtime_entries() -> None:
    catalog = _catalog()

    assert len(catalog) == 144
    assert len({asset.asset_id for asset in catalog}) == 144
    assert all(asset.review_status == "REVIEW_PENDING" for asset in catalog)
    assert all(not asset.runtime_eligible for asset in catalog)
    assert all(asset.provenance.license_status == "REVIEW_REQUIRED" for asset in catalog)


def test_gate_a_is_required_before_candidates_are_built() -> None:
    assets = tuple(_approved(item) for item in _catalog())

    context = build_topic_asset_candidate_context(
        query=_query("cat", gate_a=False),
        assets=assets,
    )

    assert context.status == "GATE_A_REQUIRED"
    assert context.miss_reason == "GATE_A_REQUIRED"
    assert not context.candidates
    assert context.authoring_queue_proposal is None


def test_long_tail_topic_returns_typed_miss() -> None:
    assets = tuple(_approved(item) for item in _catalog())

    context = build_topic_asset_candidate_context(
        query=_query("narwhal"),
        assets=assets,
    )

    assert context.status == "NO_MATCH"
    assert context.miss_reason == "NO_SEMANTIC_MATCH"
    assert not context.candidates
    assert context.authoring_queue_proposal is not None
    assert context.authoring_queue_proposal.topic_labels == ("narwhal",)


def test_style_and_role_constraints_are_applied_before_ai_context() -> None:
    asset = _approved(next(item for item in _catalog() if item.asset_id.endswith(".microscope.v1")))
    context = build_topic_asset_candidate_context(
        query=_query(
            "microscope",
            styleProfileId="incompatible-style",
            requestedRoles=("SUBJECT",),
        ),
        assets=(asset,),
    )

    assert context.status == "NO_MATCH"
    assert context.miss_reason == "NO_COMPATIBLE_APPROVED_ASSETS"


def test_model_output_is_restricted_to_supplied_approved_ids() -> None:
    all_assets = _catalog()
    cat = _approved(next(item for item in all_assets if item.asset_id == "topic.animal.cat.v1"))
    context = build_topic_asset_candidate_context(query=_query("cat"), assets=(cat,))

    picked = validate_topic_asset_selection(
        output={"assetIds": [cat.asset_id], "noMatch": False},
        context=context,
        catalog_assets=(cat,),
    )
    assert picked.asset_ids == (cat.asset_id,)

    with pytest.raises(ValueError, match="unknown, unapproved, or out-of-context"):
        validate_topic_asset_selection(
            output={"assetIds": ["topic.animal.dog.v1"], "noMatch": False},
            context=context,
            catalog_assets=all_assets,
        )


@pytest.mark.parametrize(
    "output",
    [
        {"assetIds": ["topic.animal.cat.v1"], "noMatch": True},
        {"assetIds": ["topic.animal.cat.v1", "topic.animal.cat.v1"], "noMatch": False},
        {"assetIds": [], "noMatch": False},
        {"assetIds": ["topic.animal.cat.v1"], "noMatch": False, "extra": "not allowed"},
    ],
)
def test_malformed_duplicate_or_inconsistent_model_output_is_rejected(
    output: dict[str, object],
) -> None:
    cat = _approved(next(item for item in _catalog() if item.asset_id == "topic.animal.cat.v1"))
    context = build_topic_asset_candidate_context(query=_query("cat"), assets=(cat,))

    with pytest.raises(ValueError):
        validate_topic_asset_selection(output=output, context=context, catalog_assets=(cat,))


def test_pending_descriptor_cannot_be_marked_runtime_eligible() -> None:
    pending = next(item for item in _catalog() if item.asset_id == "topic.animal.cat.v1")
    data = pending.model_dump(mode="json", by_alias=True)
    data["runtimeEligible"] = True

    with pytest.raises(ValidationError, match="approved or applied"):
        TopicAssetDescriptorV1.model_validate(data)


def test_selector_input_rejects_media_fields() -> None:
    with pytest.raises(ValidationError):
        AdultConfirmedTopicV1.model_validate(
            {
                "gateAConfirmed": True,
                "topicLabels": ["mèo"],
                "imageUri": "private://child-drawing",
            }
        )
