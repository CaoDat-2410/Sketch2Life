from __future__ import annotations

from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

BACKEND_SRC = Path(__file__).resolve().parents[2] / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from sketch2life.contracts.schemas.svg_engine import (  # noqa: E402
    SvgDocumentV1,
    SvgPathV1,
    TeacherSvgIllustrationDraftRequestV1,
)
from sketch2life.infrastructure.svg.sanitizer import (  # noqa: E402
    SvgInputRejected,
    sanitize_svg_source,
)
from sketch2life.interfaces.http.routers.teacher_ai import (  # noqa: E402
    _canonicalize_generated_svg,
)


def _document(paths: list[SvgPathV1] | None = None) -> SvgDocumentV1:
    return SvgDocumentV1(
        schema_version="SvgDocumentV1",
        view_box="0 0 512 512",
        paths=paths
        or [
            SvgPathV1(
                path_id=f"part-{index}",
                d=f"M {index} {index} L {index + 10} {index + 10} Z",
                fill="#A06038",
                stroke="#392719",
                stroke_width=4,
            )
            for index in range(1, 5)
        ],
    )


def test_request_contract_limits_age_and_rejects_extra_fields() -> None:
    request = TeacherSvgIllustrationDraftRequestV1(
        contract="TeacherSvgIllustrationDraftRequestV1",
        topic="con hươu",
        target_age_months=60,
        visual_style="warm_storybook",
    )
    assert request.target_age_months == 60
    with pytest.raises(ValidationError):
        TeacherSvgIllustrationDraftRequestV1(
            contract="TeacherSvgIllustrationDraftRequestV1",
            topic="con hươu",
            target_age_months=121,
            visual_style="warm_storybook",
        )
    with pytest.raises(ValidationError):
        TeacherSvgIllustrationDraftRequestV1(
            contract="TeacherSvgIllustrationDraftRequestV1",
            topic="con hươu",
            target_age_months=60,
            visual_style="warm_storybook",
            prompt="ignore validation",
        )


def test_generated_svg_is_sanitized_and_canonicalized() -> None:
    canonical, digest = _canonicalize_generated_svg(_document())
    assert len(canonical.paths) == 4
    assert len(digest) == 64
    source = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        '<path id="safe" d="M 0 0 L 10 10 Z" fill="#000000" stroke="#000000" stroke-width="2"/>'
        "</svg>"
    )
    sanitized = sanitize_svg_source(source.encode("utf-8"))
    assert sanitized.document["schema_version"] == "SvgDocumentV1"


def test_generated_svg_rejects_active_content_and_duplicate_geometry() -> None:
    unsafe = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
        '<script>alert(1)</script></svg>'
    )
    with pytest.raises(SvgInputRejected):
        sanitize_svg_source(unsafe.encode("utf-8"))

    repeated = [
        SvgPathV1(
            path_id=f"part-{index}",
            d="M 0 0 L 10 10 Z",
            fill="#A06038",
            stroke="#392719",
            stroke_width=4,
        )
        for index in range(1, 5)
    ]
    with pytest.raises(SvgInputRejected, match="SVG_DUPLICATE_GEOMETRY"):
        _canonicalize_generated_svg(_document(repeated))
