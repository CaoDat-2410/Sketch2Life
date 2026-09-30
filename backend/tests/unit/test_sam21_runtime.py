from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21ImageSegmenter,
    Sam21MaskRejectedError,
    Sam21Prompt,
    Sam21RuntimeConfig,
)


def _image_png() -> bytes:
    image = Image.new("RGB", (40, 40), "white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_bad_part_prompt_does_not_discard_successful_subject_mask() -> None:
    numpy = pytest.importorskip("numpy")

    class Predictor:
        image: object | None = None
        calls = 0

        def set_image(self, image: object) -> None:
            self.image = image

        def predict(self, **kwargs: object) -> tuple[object, object, None]:
            assert kwargs["multimask_output"] is True
            self.calls += 1
            mask = numpy.zeros((40, 40), dtype=bool)
            if self.calls == 1:
                mask[8:32, 8:32] = True
            # Return an empty mask for the part request to exercise per-part degradation.
            return numpy.asarray([mask]), numpy.asarray([0.9]), None

    predictor = Predictor()
    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=predictor,
    )
    parent = SourceRegionV1(x=0.1, y=0.1, width=0.8, height=0.8)
    part = SourceRegionV1(x=0.2, y=0.2, width=0.4, height=0.4)

    outputs = runtime.segment_many(
        _image_png(),
        (
            Sam21Prompt(prompt_region=parent, positive_points=(), negative_points=()),
            Sam21Prompt(prompt_region=part, positive_points=(), negative_points=()),
        ),
    )

    assert predictor.calls == 2
    assert outputs[0] is not None
    assert outputs[0].source_region.width == 0.6
    assert outputs[1] is None


def test_multimask_selection_rejects_high_score_candidate_that_violates_points() -> None:
    numpy = pytest.importorskip("numpy")

    class Predictor:
        def set_image(self, _image: object) -> None:
            pass

        def predict(self, **kwargs: object) -> tuple[object, object, None]:
            assert kwargs["multimask_output"] is True
            distractor = numpy.zeros((40, 40), dtype=bool)
            distractor[4:36, 4:36] = True
            target = numpy.zeros((40, 40), dtype=bool)
            target[10:20, 10:20] = True
            return numpy.asarray([distractor, target]), numpy.asarray([0.99, 0.76]), None

    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=Predictor(),
    )
    output = runtime.segment(
        _image_png(),
        prompt_region=SourceRegionV1(x=0.15, y=0.15, width=0.65, height=0.65),
        positive_points=((0.3, 0.3),),
        negative_points=((0.7, 0.7),),
    )

    with Image.open(BytesIO(output.mask_png)) as mask_image:
        selected = numpy.asarray(mask_image) > 0
    assert selected[12, 12]
    assert not selected[28, 28]
    assert output.confidence == 0.76


def test_multimask_selection_rejects_candidate_missing_grounded_thin_detail() -> None:
    numpy = pytest.importorskip("numpy")

    class Predictor:
        def set_image(self, _image: object) -> None:
            pass

        def predict(self, **kwargs: object) -> tuple[object, object, None]:
            assert kwargs["multimask_output"] is True
            distractor = numpy.zeros((40, 40), dtype=bool)
            distractor[10:30, 10:30] = True
            distractor[32:35, 32:35] = True
            missing_thin_detail = numpy.zeros((40, 40), dtype=bool)
            missing_thin_detail[10:30, 10:30] = True
            complete = missing_thin_detail.copy()
            complete[18, 8:10] = True
            return (
                numpy.asarray([distractor, missing_thin_detail, complete]),
                numpy.asarray([0.99, 0.90, 0.80]),
                None,
            )

    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=Predictor(),
    )
    output = runtime.segment(
        _image_png(),
        prompt_region=SourceRegionV1(x=0.1, y=0.1, width=0.7, height=0.7),
        positive_points=((0.5, 0.5), (8.5 / 40, 18.5 / 40)),
        negative_points=((33.5 / 40, 33.5 / 40),),
    )

    with Image.open(BytesIO(output.mask_png)) as mask_image:
        selected = numpy.asarray(mask_image) > 0
    assert selected[18, 8]
    assert selected[18, 9]
    assert not selected[33, 33]
    assert output.confidence == 0.80


def test_multimask_selection_returns_typed_rejection_when_no_candidate_matches_prompt() -> None:
    numpy = pytest.importorskip("numpy")

    class Predictor:
        def set_image(self, _image: object) -> None:
            pass

        def predict(self, **_kwargs: object) -> tuple[object, object, None]:
            mask = numpy.zeros((40, 40), dtype=bool)
            mask[10:20, 10:20] = True
            return numpy.asarray([mask]), numpy.asarray([0.95]), None

    runtime = Sam21ImageSegmenter(
        Sam21RuntimeConfig(checkpoint=None, model_config="", device="cpu"),
        predictor=Predictor(),
    )
    with pytest.raises(Sam21MaskRejectedError, match="no valid mask"):
        runtime.segment(
            _image_png(),
            prompt_region=None,
            positive_points=((0.3, 0.3),),
            negative_points=((0.35, 0.35),),
        )
