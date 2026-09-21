"""Deterministic shortlist and allowlist validation for FEAT-028 topic assets.

This service is safe to call before a model ranker: it accepts only adult-confirmed text,
uses reviewed local metadata, and never reads source artwork or provider configuration.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import unicodedata
from pathlib import Path
from typing import Any, Literal

from sketch2life.contracts.schemas.pixi_topic_asset_selection import (
    AdultConfirmedTopicV1,
    TopicAssetAuthoringQueueProposalV1,
    TopicAssetCandidateContextV1,
    TopicAssetCandidateV1,
    TopicAssetDescriptorV1,
    TopicAssetSelectionOutputV1,
)

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "and",
    "with",
    "in",
    "on",
    "to",
    "mot",
    "con",
    "cai",
    "buc",
    "tranh",
    "ve",
    "dang",
    "va",
}


def load_topic_asset_catalog(path: Path) -> tuple[TopicAssetDescriptorV1, ...]:
    """Load and validate the internal v2 catalog; never changes any asset state."""
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read the topic asset catalog") from exc
    if not isinstance(catalog, dict) or (
        catalog.get("schemaName") != "PixiTopicAssetCatalogV2"
        or catalog.get("schemaVersion") != "2.0"
        or catalog.get("catalogVersion") != "2.0.0"
    ):
        raise ValueError("unsupported topic asset catalog schema or version")
    records = catalog.get("assets")
    if not isinstance(records, list):
        raise ValueError("topic asset catalog assets must be an array")
    try:
        assets = tuple(TopicAssetDescriptorV1.model_validate(item) for item in records)
    except Exception as exc:
        raise ValueError("topic asset catalog contains an invalid descriptor") from exc
    ids = tuple(asset.asset_id for asset in assets)
    if len(set(ids)) != len(ids):
        raise ValueError("topic asset catalog contains duplicate asset IDs")
    feature_root = path.resolve().parents[2]
    verified_files: dict[Path, tuple[str, int, int]] = {}
    for asset in assets:
        asset_path = (feature_root / asset.provenance.asset_file).resolve()
        try:
            asset_path.relative_to(feature_root)
        except ValueError as exc:
            raise ValueError("catalog asset path escapes its feature root") from exc
        if asset_path not in verified_files:
            try:
                data = asset_path.read_bytes()
            except OSError as exc:
                raise ValueError("catalog references a missing local atlas") from exc
            if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError("catalog references an invalid PNG atlas")
            width, height = struct.unpack(">II", data[16:24])
            verified_files[asset_path] = (hashlib.sha256(data).hexdigest(), width, height)
        digest, width, height = verified_files[asset_path]
        frame = asset.frame
        if digest != asset.provenance.atlas_sha256:
            raise ValueError("catalog atlas hash does not match its provenance")
        if frame.x + frame.width > width or frame.y + frame.height > height:
            raise ValueError("catalog frame bounds exceed the source atlas")
    return assets


def build_topic_asset_candidate_context(
    *,
    query: AdultConfirmedTopicV1,
    assets: tuple[TopicAssetDescriptorV1, ...],
) -> TopicAssetCandidateContextV1:
    """Return stable top-K approved candidates, or a typed safe miss."""
    if not query.gate_a_confirmed:
        return TopicAssetCandidateContextV1(
            status="GATE_A_REQUIRED",
            confirmedTopicLabels=query.topic_labels,
            confirmedTopicTags=query.topic_tags,
            missReason="GATE_A_REQUIRED",
        )

    approved = tuple(
        asset
        for asset in assets
        if asset.runtime_eligible and asset.review_status in {"APPROVED", "APPLIED"}
    )
    if not approved:
        return _miss_context(query, "NO_APPROVED_ASSETS")
    eligible = tuple(
        asset
        for asset in approved
        if query.style_profile_id in asset.style_profile_ids
        and (not query.requested_roles or asset.render_role in query.requested_roles)
    )
    if not eligible:
        return _miss_context(query, "NO_COMPATIBLE_APPROVED_ASSETS")

    terms = (*query.topic_labels, *query.topic_tags)
    scored = [
        (score, asset.asset_id, asset)
        for asset in eligible
        if (score := _match_score(terms, asset)) > 0
    ]
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return _miss_context(query, "NO_SEMANTIC_MATCH")

    candidates = tuple(
        _to_candidate(asset) for _score, _asset_id, asset in scored[: query.max_candidates]
    )
    return TopicAssetCandidateContextV1(
        status="READY",
        confirmedTopicLabels=query.topic_labels,
        confirmedTopicTags=query.topic_tags,
        candidates=candidates,
    )


def _miss_context(
    query: AdultConfirmedTopicV1,
    reason: Literal["NO_APPROVED_ASSETS", "NO_COMPATIBLE_APPROVED_ASSETS", "NO_SEMANTIC_MATCH"],
) -> TopicAssetCandidateContextV1:
    return TopicAssetCandidateContextV1(
        status="NO_MATCH",
        confirmedTopicLabels=query.topic_labels,
        confirmedTopicTags=query.topic_tags,
        missReason=reason,
        authoringQueueProposal=TopicAssetAuthoringQueueProposalV1(
            topicLabels=query.topic_labels,
            topicTags=query.topic_tags,
            reasonCode=reason,
        ),
    )


def validate_topic_asset_selection(
    *,
    output: dict[str, Any] | str,
    context: TopicAssetCandidateContextV1,
    catalog_assets: tuple[TopicAssetDescriptorV1, ...],
) -> TopicAssetSelectionOutputV1:
    """Parse a model response and enforce shortlist, approval, role, and style allowlists."""
    if context.status != "READY":
        raise ValueError("cannot accept model picks when candidate context is not ready")
    try:
        raw = json.loads(output) if isinstance(output, str) else output
        selection = TopicAssetSelectionOutputV1.model_validate(raw)
    except Exception as exc:
        raise ValueError("model selection does not match PixiTopicAssetSelectionOutputV1") from exc

    candidate_ids = {candidate.asset_id for candidate in context.candidates}
    by_id = {asset.asset_id: asset for asset in catalog_assets}
    for asset_id in selection.asset_ids:
        asset = by_id.get(asset_id)
        if (
            asset_id not in candidate_ids
            or asset is None
            or not asset.runtime_eligible
            or asset.review_status not in {"APPROVED", "APPLIED"}
        ):
            raise ValueError("model selected an unknown, unapproved, or out-of-context asset ID")
    return selection


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold().replace("đ", "d"))
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(_WORD_RE.findall(without_marks))


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if token not in _STOPWORDS}


def _match_score(
    terms: tuple[str, ...],
    asset: TopicAssetDescriptorV1,
) -> int:
    searchable_phrases = (
        asset.label.en,
        asset.label.vi,
        *asset.aliases.en,
        *asset.aliases.vi,
    )
    normalized_phrases = {_normalize(value) for value in searchable_phrases}
    normalized_tags = {_normalize(value) for value in asset.topic_tags}
    asset_tokens = set().union(
        *(_tokens(value) for value in (*searchable_phrases, *asset.topic_tags))
    )
    best = 0
    for term in terms:
        normalized = _normalize(term)
        if not normalized:
            continue
        if normalized in normalized_phrases:
            best = max(best, 100)
            continue
        if normalized in normalized_tags:
            best = max(best, 90)
            continue
        query_tokens = _tokens(term)
        if query_tokens:
            overlap = len(query_tokens & asset_tokens)
            if overlap:
                best = max(best, 30 + round(50 * overlap / len(query_tokens)))
    return best


def _to_candidate(asset: TopicAssetDescriptorV1) -> TopicAssetCandidateV1:
    return TopicAssetCandidateV1(
        assetId=asset.asset_id,
        family=asset.family,
        label=asset.label,
        aliases=asset.aliases,
        visualDescription=asset.visual_description,
        topicTags=asset.topic_tags,
        renderRole=asset.render_role,
        confusableWith=asset.confusable_with,
        intendedUse=asset.intended_use,
    )


__all__ = [
    "build_topic_asset_candidate_context",
    "load_topic_asset_catalog",
    "validate_topic_asset_selection",
]
