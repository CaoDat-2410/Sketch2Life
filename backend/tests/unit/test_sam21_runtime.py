from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.infrastructure.ai.sam21_runtime import (
    Sam21ImageSegmenter,
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

        def predict(self, **_kwargs: object) -> tuple[object, object, None]:
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
