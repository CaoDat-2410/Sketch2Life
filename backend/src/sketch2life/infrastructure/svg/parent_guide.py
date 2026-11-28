"""Build private SVG drawing guides for Parent sessions from the project's shape recipes (FEAT-097)."""

from __future__ import annotations

import hashlib
from typing import Any
from uuid import uuid4

from sketch2life.contracts.schemas.svg_engine import (
    SvgTopicStrokeGuideDerivationV1,
    SvgTopicStrokeGuidePathLineageV1,
    SvgTopicStrokeGuideSourceDraftResponseV1,
    SvgTopicStrokeGuideV1,
)
from sketch2life.infrastructure.svg.recipe_guide import build_recipe_guide
from sketch2life.infrastructure.svg.sanitizer import canonical_json_bytes


class ParentSvgGuideUnavailable(ValueError):
    """The request cannot name a subject."""


def build_parent_svg_guide(
    *, topic: str, intended_subject: str | None, difficulty: str = "beginner", request_id: str | None = None
) -> dict[str, Any] | None:
    """The recipe of the asked level named by the adult's idea, else by the topic; ``None`` when neither names one."""
    normalized_topic = " ".join(topic.split())
    subject = " ".join((intended_subject or "").split())
    if len(normalized_topic) < 2 or len(normalized_topic) > 120 or len(subject) > 160:
        raise ParentSvgGuideUnavailable("PARENT_SVG_GUIDE_INPUT_INVALID")

    source_guide = build_recipe_guide([text for text in (subject, normalized_topic) if text], difficulty)
    if source_guide is None:
        return None

    request_id = request_id or str(uuid4())
    generated = source_guide.generated
    document = generated.document.model_dump(mode="json")
    document_sha256 = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
    guide = SvgTopicStrokeGuideV1(
        guide_id=request_id,
        title_vi=generated.title_vi,
        parts=generated.parts,
        stages=generated.stages,
    )
    derivation = SvgTopicStrokeGuideDerivationV1(
        engine_id=source_guide.engine_id,
        engine_revision=source_guide.engine_revision,
        source_guide_uri=source_guide.source_guide_uri,
        source_guide_sha256=source_guide.source_guide_sha256,
        method=source_guide.derivation_method,
        source_path_count=source_guide.source_path_count,
        path_lineage=[
            SvgTopicStrokeGuidePathLineageV1.model_validate(item)
            for item in source_guide.path_lineage
        ],
    )
    response = SvgTopicStrokeGuideSourceDraftResponseV1(
        request_id=request_id,
        topic=normalized_topic,
        intended_subject=subject or None,
        status="DRAFT",
        review_required=True,
        persisted=False,
        generation_source="CURATED_SOURCE_DERIVATION",
        derivation=derivation,
        reference_source=source_guide.reference_source,
        reference_illustration=source_guide.reference_illustration,
        document=document,
        document_sha256=document_sha256,
        guide=guide,
        path_count=len(generated.document.paths),
        stage_count=len(generated.stages),
        quality_gates_passed=[
            "RECIPE_LEVEL_RULES_PASSED",
            "BIGGEST_PART_FIRST_AND_CONNECTED",
            "INSTRUCTION_NAMES_ITS_PART",
            "ADAPTIVE_4_TO_8_STAGES",
            "RECIPE_PROVENANCE_INCLUDED",
            "PRIVATE_DRAFT_REQUIRES_ADULT_REVIEW",
        ],
    )
    return response.model_dump(mode="json")


__all__ = ["ParentSvgGuideUnavailable", "build_parent_svg_guide"]
