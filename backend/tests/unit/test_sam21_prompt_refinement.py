from __future__ import annotations

import hashlib
from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.lightning_sam21 import (
    LightningSam21SegmentationAdapter,
    propose_colored_component_prompt,
)
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21ImageSegmenter,
    Sam21Prompt,
    Sam21RuntimeConfig,
    _largest_component_fraction,
)


def _drawing_png() -> bytes:
    image = Image.new("RGB", (80, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((18, 14, 50, 48), fill=(230, 100, 20))
    draw.line((47, 30, 60, 30), fill=(20, 110, 220), width=4)
    return _png(image)


def _png(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _point_pixel(point: tuple[float, float], image: Image.Image) -> tuple[int, int]:
    return min(image.width - 1, int(point[0] * image.width)), min(
        image.height - 1, int(point[1] * image.height)
    )


def test_prompt_proposal_anchors_ink_and_only_uses_clear_paper_as_negative() -> None:
    image_bytes = _drawing_png()
    with Image.open(BytesIO(image_bytes)) as opened:
        image = opened.convert("RGB")
    region = SourceRegionV1(x=0.15, y=0.1, width=0.6, height=0.7)

    proposal = propose_colored_component_prompt(image_bytes, preferred_region=region)

    assert proposal.prompt_region == region
    assert len(proposal.positive_points) == 1
    positive = image.getpixel(_point_pixel(proposal.positive_points[0], image))
    assert max(positive) - min(positive) >= 20
    assert len(proposal.negative_points) == 1
    negative_x, negative_y = _point_pixel(proposal.negative_points[0], image)
    negative = image.getpixel((negative_x, negative_y))
    assert max(negative) - min(negative) <= 18
    assert sum(negative) / 3 >= 220
    assert not (region.x <= proposal.negative_points[0][0] <= region.x + region.width)


def test_prompt_proposal_omits_negative_when_no_clear_paper_exists() -> None:
    image = Image.new("RGB", (80, 64), (120, 120, 120))
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 12, 60, 50), fill=(40, 90, 140))
    proposal = propose_colored_component_prompt(_png(image))

    assert proposal.prompt_region is not None
    assert proposal.positive_points
    assert proposal.negative_points == ()


def test_prompt_normalization_round_trips_for_large_non_square_source() -> None:
    image = Image.new("RGB", (1200, 800), "white")
    ImageDraw.Draw(image).rectangle((300, 220, 780, 580), fill=(225, 80, 15))
    region = SourceRegionV1(x=0.2, y=0.2, width=0.5, height=0.55)

    proposal = propose_colored_component_prompt(
        _png(image), preferred_region=region, include_negative=False
    )

    assert len(proposal.positive_points) == 1
    normalized_x, normalized_y = proposal.positive_points[0]
    source_x, source_y = int(normalized_x * image.width), int(normalized_y * image.height)
    assert 300 <= source_x <= 780
    assert 220 <= source_y <= 580
    assert 0.0 < normalized_x < 1.0
    assert 0.0 < normalized_y < 1.0


def test_component_consistency_distinguishes_fragmented_masks() -> None:
    numpy = pytest.importorskip("numpy")
    connected = numpy.zeros((20, 20), dtype=bool)
    connected[3:17, 3:17] = True
    fragmented = connected.copy()
    fragmented[3:17, 3:17] = False
    fragmented[3:8, 3:8] = True
    fragmented[9:14, 9:14] = True

    assert _largest_component_fraction(connected, numpy=numpy) == 1.0
    assert _largest_component_fraction(fragmented, numpy=numpy) == 0.5


def test_part_seed_outside_accepted_subject_is_not_forwarded_to_sam() -> None:
    numpy = pytest.importorskip("numpy")
    image_bytes = _png(Image.new("RGB", (40, 40), "white"))
    parent_mask = numpy.zeros((40, 40), dtype=bool)
    parent_mask[10:20, 10:20] = True

    class Predictor:
        calls = 0

        def set_image(self, _image: object) -> None:
            pass

        def predict(self, **kwargs: object) -> tuple[object, object, None]:
            self.calls += 1
            if self.calls == 2:
                assert kwargs.get("point_coords") is None
                mask = parent_mask
            else:
                assert kwargs["multimask_output"] is True
                mask = parent_mask
            return numpy.asarray([mask]), numpy.asarray([0.9]), None

    predictor = Predictor()
    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=predictor,
    )
    region = SourceRegionV1(x=0.1, y=0.1, width=0.8, height=0.8)

    outputs = runtime.segment_many(
        image_bytes,
        (
            Sam21Prompt(region, ((0.35, 0.35),), ()),
            Sam21Prompt(
                region,
                ((0.75, 0.75),),
                (),
                refinement_group="part",
            ),
        ),
    )

    assert predictor.calls == 2
    assert outputs[0] is not None
    assert outputs[1] is not None


def test_adapter_forwards_derived_subject_points_without_exposing_provider_output() -> None:
    image = _drawing_png()
    digest = hashlib.sha256(image).hexdigest()

    class Transport:
        payload: dict[str, object] | None = None

        def post_json(self, _path: str, payload: dict[str, object]) -> dict[str, object]:
            self.payload = payload
            return {
                "contractName": "Sam21SegmentationResponseV1",
                "contractVersion": "1.0",
                "status": "FAILED",
                "adapterId": "sam2.1-hiera-small",
                "adapterVersion": "1",
                "sourceSha256": digest,
                "failureCode": "MASK_REJECTED",
                "retryable": False,
            }

    transport = Transport()
    adapter = LightningSam21SegmentationAdapter(
        transport=transport,
        artifact_loader=lambda _ref: image,
    )
    from sketch2life.application.ports.segmentation import SubjectSegmentationRequest

    result = adapter.segment(
        SubjectSegmentationRequest(
            session_id="s",
            source_artifact_ref="source",
            source_sha256=digest,
            target_id="anchor-bird",
            target_label="con chim",
            target_confidence=0.9,
            semantic_tags=("animal",),
        )
    )

    assert result is None
    assert transport.payload is not None
    assert transport.payload["prompt_region"] is not None
    assert len(transport.payload["positive_points"]) == 1  # type: ignore[arg-type]
    assert len(transport.payload["negative_points"]) == 1  # type: ignore[arg-type]


def test_refinement_uses_logits_and_is_globally_bounded_to_two_extra_predictions() -> None:
    numpy = pytest.importorskip("numpy")
    image = Image.new("RGB", (40, 40), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 19, 19), fill=(220, 80, 15))
    draw.line((19, 14, 24, 14), fill=(20, 100, 220), width=1)
    image_bytes = _png(image)
    initial_mask = numpy.zeros((40, 40), dtype=bool)
    initial_mask[10:20, 10:20] = True
    refined_mask = initial_mask.copy()
    refined_mask[14, 20:25] = True

    class Predictor:
        calls = 0
        refinements = 0

        def set_image(self, _image: object) -> None:
            pass

        def predict(self, **kwargs: object) -> tuple[object, object, object]:
            self.calls += 1
            if kwargs.get("mask_input") is None:
                assert kwargs["multimask_output"] is True
                masks = numpy.asarray([initial_mask, initial_mask, initial_mask])
                scores = numpy.asarray([0.90, 0.89, 0.88])
                logits = numpy.zeros((3, 16, 16), dtype=numpy.float32)
                return masks, scores, logits
            self.refinements += 1
            assert kwargs["multimask_output"] is False
            assert numpy.asarray(kwargs["mask_input"]).shape == (1, 16, 16)
            coords = numpy.asarray(kwargs["point_coords"])
            labels = numpy.asarray(kwargs["point_labels"])
            assert any(
                labels[index] == 1 and coords[index, 0] > 0.5
                for index in range(len(labels))
            )
            return (
                numpy.asarray([refined_mask]),
                numpy.asarray([0.96]),
                numpy.zeros((1, 16, 16), dtype=numpy.float32),
            )

    predictor = Predictor()
    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=predictor,
    )
    region = SourceRegionV1(x=0.1, y=0.1, width=0.75, height=0.75)
    subject_prompt = Sam21Prompt(region, ((0.35, 0.35),), ())
    part_prompt = Sam21Prompt(region, ((0.35, 0.35),), (), refinement_group="part")

    outputs = runtime.segment_many(image_bytes, (subject_prompt, part_prompt, part_prompt))

    assert predictor.calls == 5  # Three initial calls plus the hard two-refinement cap.
    assert predictor.refinements == 2
    assert all(output is not None for output in outputs)
    assert outputs[0] is not None
    with Image.open(BytesIO(outputs[0].mask_png)) as refined:
        assert numpy.asarray(refined)[14, 22] == 255
    assert outputs[2] is not None
    with Image.open(BytesIO(outputs[2].mask_png)) as unrefined:
        assert numpy.asarray(unrefined)[14, 22] == 0
