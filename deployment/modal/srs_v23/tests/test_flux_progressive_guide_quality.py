from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

MODAL_DIR = Path(__file__).resolve().parents[1]
if str(MODAL_DIR) not in sys.path:
    sys.path.insert(0, str(MODAL_DIR))
FLUX_SPEC = importlib.util.spec_from_file_location(
    "sketch2life_modal_flux3_progressive_quality_test",
    MODAL_DIR / "flux_image_app.py",
)
assert FLUX_SPEC is not None and FLUX_SPEC.loader is not None
flux_image_app = importlib.util.module_from_spec(FLUX_SPEC)
FLUX_SPEC.loader.exec_module(flux_image_app)


def _draw_panels(
    *,
    shift: int = 0,
    redraw: bool = False,
    repeat_last: bool = False,
    repeat_all: bool = False,
    thinner_middle: bool = False,
) -> Image.Image:
    panel_size = 256
    image = Image.new("RGB", (panel_size * 3, panel_size), "white")
    for index in range(3):
        draw = ImageDraw.Draw(image)
        left = index * panel_size
        effective_index = 0 if repeat_all else 1 if repeat_last and index == 2 else index
        if effective_index == 0:
            draw.line((left + 80, 55, left + 80, 200), fill="black", width=3)
        elif effective_index == 1:
            x = 80 + shift
            width = 2 if thinner_middle else 3
            crossbar_width = 1 if thinner_middle else 3
            draw.line((left + x, 55, left + x, 200), fill="black", width=width)
            draw.line((left + 80, 135, left + 178, 135), fill="black", width=crossbar_width)
        else:
            if redraw:
                draw.line((left + 190, 45, left + 190, 210), fill="black", width=6)
                draw.line((left + 190, 85, left + 225, 85), fill="black", width=6)
                draw.line((left + 195, 165, left + 230, 195), fill="black", width=6)
            else:
                x = 80 + shift
                draw.line((left + x, 55, left + x, 200), fill="black", width=3)
                draw.line((left + 80, 135, left + 178, 135), fill="black", width=3)
                draw.ellipse((left + 112, 94, left + 150, 132), outline="black", width=3)
    return image


def _draw_eight_step_panels(
    *,
    low_retention_transitions: tuple[int, ...] = (1,),
    drop_retained_stroke: bool = False,
    low_retention_line_fraction: float = 1.0,
) -> Image.Image:
    panel_size = 256
    image = Image.new("RGB", (panel_size * 4, panel_size * 2), "white")
    strokes: list[tuple[str, tuple[int, ...]]] = []
    for index in range(8):
        left = (index % 4) * panel_size
        top = (index // 4) * panel_size
        if index == 0:
            strokes = [
                ("line", (x, 60, x, 196, 3))
                for x in (30, 58, 86, 114, 142, 170, 198)
            ]
            strokes.extend(
                ("line", (60, y, 220, y, 3)) for y in (85, 130, 175)
            )
        elif index in low_retention_transitions:
            if drop_retained_stroke and index == 1:
                strokes = []
            else:
                strokes = strokes[:1]
                if index == 1 and low_retention_line_fraction < 1.0:
                    retained_end = 60 + round(136 * low_retention_line_fraction)
                    strokes[0] = ("line", (30, 60, 30, retained_end, 3))
            rows = (25, 45, 215, 235) if index == 1 else (85, 120, 155, 190)
            strokes.extend(("line", (60, y, 220, y, 3)) for y in rows)
        else:
            strokes = list(strokes)
            if index >= 2:
                offset = index - 2
                center_x = 120 + (offset % 3) * 28
                center_y = 75 + (offset // 3) * 34
                strokes.append(("ellipse", (center_x - 9, center_y - 9, center_x + 9, center_y + 9, 3)))

        draw = ImageDraw.Draw(image)
        for kind, coordinates in strokes:
            if kind == "line":
                draw.line(
                    (left + coordinates[0], top + coordinates[1], left + coordinates[2], top + coordinates[3]),
                    fill="black",
                    width=coordinates[4],
                )
            else:
                draw.ellipse(
                    (left + coordinates[0], top + coordinates[1], left + coordinates[2], top + coordinates[3]),
                    outline="black",
                    width=coordinates[4],
                )
    return image


def test_progressive_guide_allows_small_cumulative_stroke_shift() -> None:
    flux_image_app._validate_progressive_panels(
        _draw_panels(shift=3),
        3,
        {"columns": 3, "rows": 1},
    )


def test_progressive_guide_allows_moderate_flux_line_drift() -> None:
    flux_image_app._validate_progressive_panels(
        _draw_panels(shift=8),
        3,
        {"columns": 3, "rows": 1},
    )


def test_progressive_guide_allows_new_strokes_when_total_ink_does_not_grow() -> None:
    flux_image_app._validate_progressive_panels(
        _draw_panels(thinner_middle=True),
        3,
        {"columns": 3, "rows": 1},
    )


def test_progressive_guide_allows_one_quiet_transition_when_the_sequence_progresses() -> None:
    flux_image_app._validate_progressive_panels(
        _draw_panels(repeat_last=True),
        3,
        {"columns": 3, "rows": 1},
    )


def test_progressive_guide_still_rejects_a_sequence_with_no_progress() -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="NOT_CUMULATIVE"):
        flux_image_app._validate_progressive_panels(
            _draw_panels(repeat_all=True),
            3,
            {"columns": 3, "rows": 1},
        )


def test_progressive_guide_still_rejects_a_full_redraw() -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="STROKES_CHANGED"):
        flux_image_app._validate_progressive_panels(
            _draw_panels(redraw=True),
            3,
            {"columns": 3, "rows": 1},
        )


def test_progressive_guide_still_rejects_materially_moved_strokes() -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="STROKES_CHANGED"):
        flux_image_app._validate_progressive_panels(
            _draw_panels(shift=12),
            3,
            {"columns": 3, "rows": 1},
        )


def test_eight_step_guide_allows_one_transition_between_hard_and_soft_floors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    flux_image_app._validate_progressive_panels(
        _draw_eight_step_panels(),
        8,
        {"columns": 4, "rows": 2},
    )

    diagnostics = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    low_transition = next(item for item in diagnostics if item["transition_index"] == 1)
    assert 0.08 <= low_transition["measured_overlap"] < 0.20
    assert low_transition == {
        "event": "progressive_panel_transition_quality",
        "transition_index": 1,
        "measured_overlap": low_transition["measured_overlap"],
        "soft_threshold": 0.2,
        "hard_floor": 0.08,
        "previous_coverage": low_transition["previous_coverage"],
        "current_coverage": low_transition["current_coverage"],
    }


def test_eight_step_guide_still_rejects_two_low_retention_transitions() -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="STROKES_CHANGED"):
        flux_image_app._validate_progressive_panels(
            _draw_eight_step_panels(low_retention_transitions=(1, 2)),
            8,
            {"columns": 4, "rows": 2},
        )


def test_eight_step_guide_still_rejects_retention_below_hard_floor() -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="STROKES_CHANGED"):
        flux_image_app._validate_progressive_panels(
            _draw_eight_step_panels(drop_retained_stroke=True),
            8,
            {"columns": 4, "rows": 2},
        )


def test_eight_step_guide_rejects_one_transition_below_eight_percent_floor(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(flux_image_app.WorkerContractError, match="STROKES_CHANGED"):
        flux_image_app._validate_progressive_panels(
            _draw_eight_step_panels(low_retention_line_fraction=0.70),
            8,
            {"columns": 4, "rows": 2},
        )

    diagnostics = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    low_transition = next(item for item in diagnostics if item["transition_index"] == 1)
    assert low_transition["measured_overlap"] < 0.08
    assert low_transition["hard_floor"] == 0.08
