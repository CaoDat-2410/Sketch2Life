"""Preview endpoint for the bounded educational storyboard stage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from sketch2life.application.services.whiteboard_storyboard import (
    WhiteboardStoryboardGenerator,
)
from sketch2life.contracts.schemas.whiteboard_storyboard import (
    WhiteboardStoryboardPreviewRequestV1,
    WhiteboardStoryboardV1,
)

router = APIRouter(prefix="/v1/whiteboard", tags=["whiteboard-storyboard"])
_generator = WhiteboardStoryboardGenerator()


@router.post(
    "/storyboards/preview",
    response_model=WhiteboardStoryboardV1,
)
def preview_storyboard(body: WhiteboardStoryboardPreviewRequestV1) -> WhiteboardStoryboardV1:
    try:
        if body.age_months is not None:
            return _generator.generate_for_age(
                subject_claim=body.subject_claim,
                feature_claim=body.feature_claim,
                age_months=body.age_months,
            )
        return _generator.generate(
            subject_claim=body.subject_claim,
            feature_claim=body.feature_claim,
            audience_band=body.audience_band,
        )
    except ValueError as error:
        detail = (
            "AGE_BAND_NOT_SUPPORTED"
            if "audience band" in str(error)
            else "UNREVIEWED_STORYBOARD_TOPIC"
        )
        raise HTTPException(status_code=422, detail=detail) from error


__all__ = ["router"]
