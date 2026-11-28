"""FEAT-066 T-2b: drawing normalization, retake state matrix, copy-forward and the analysis runner.

Offline: no database, no storage, no provider. Images are built in memory with Pillow (synthetic
shapes and noise; no real photo or child media). Behaviour against PostgreSQL and S3Mock lives in
``tests/integration/test_parent_story_inputs_postgres.py``.
"""

from __future__ import annotations

import ast
import hashlib
import io
import random
import struct
import zlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

import sketch2life.infrastructure.story_inputs.drawing as drawing_module
import sketch2life.infrastructure.story_inputs.runner as runner_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.persistence import parent_story_repository as repository_module
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    derived_asset_key,
    drawing_attach_fingerprint,
)
from sketch2life.infrastructure.story_inputs.drawing import (
    DrawingNormalizationError,
    check_source_dimensions,
    fit_within,
    normalize_drawing,
)
from sketch2life.infrastructure.story_inputs.fixtures import FixtureDrawingAnalyzer
from sketch2life.infrastructure.story_inputs.runner import (
    ParentInputJobRunner,
    candidate_from_result,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _shapes(width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), (250, 250, 240))
    for x in range(0, width, max(1, width // 8)):
        for y in range(0, height, max(1, height // 6)):
            image.putpixel((x, y), (10, 20, 30))
    return image


def _noise(width: int, height: int, seed: int = 7) -> Image.Image:
    rng = random.Random(seed)
    return Image.frombytes("RGB", (width, height), rng.randbytes(width * height * 3))


def _crafted_png(width: int, height: int) -> bytes:
    """A PNG whose header declares a huge image; only the header is read before the bomb check."""

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 1, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b""))
        + chunk(b"IEND", b"")
    )


def _decode(png: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(png))
    image.load()
    return image


# --------------------------------------------------------------------------- normalization
def test_the_derived_asset_is_rgb_png_with_exif_orientation_applied() -> None:
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90 degrees clockwise to display
    buffer = io.BytesIO()
    _shapes(60, 30).save(buffer, format="JPEG", exif=exif)
    result = normalize_drawing(buffer.getvalue(), declared_media_type="image/jpeg")
    derived = _decode(result.png_bytes)
    assert derived.format == "PNG" and derived.mode == "RGB"
    assert derived.size == (30, 60)  # the stored 60x30 pixels are shown turned
    assert (result.source_width, result.source_height) == (60, 30)
    assert result.sha256 == hashlib.sha256(result.png_bytes).hexdigest()
    assert result.size_bytes == len(result.png_bytes)


def test_webp_and_jpeg_and_png_are_accepted() -> None:
    for fmt, media_type in (
        ("WEBP", "image/webp"),
        ("JPEG", "image/jpeg"),
        ("PNG", "image/png"),
    ):
        buffer = io.BytesIO()
        _shapes(64, 48).save(buffer, format=fmt)
        result = normalize_drawing(buffer.getvalue(), declared_media_type=media_type)
        assert (result.width, result.height) == (64, 48)


def test_a_small_image_is_never_scaled_up() -> None:
    result = normalize_drawing(_png(_shapes(100, 50)), declared_media_type="image/png")
    assert (result.width, result.height) == (100, 50)


def test_a_large_image_is_scaled_down_to_two_megapixels_keeping_the_aspect_ratio() -> None:
    source = _png(Image.new("RGB", (3000, 2000), (200, 210, 220)))  # six megapixels
    result = normalize_drawing(source, declared_media_type="image/png")
    assert result.width * result.height <= 2_000_000
    assert result.width * result.height > 1_900_000
    assert abs(result.width / result.height - 1.5) < 0.01


def test_the_original_bytes_are_never_modified_or_reused() -> None:
    source = _png(_shapes(80, 80))
    before = bytes(source)
    result = normalize_drawing(source, declared_media_type="image/png")
    assert source == before
    assert result.png_bytes is not source


def test_transparency_is_composited_on_white() -> None:
    image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))
    result = normalize_drawing(_png(image), declared_media_type="image/png")
    derived = _decode(result.png_bytes)
    assert derived.getpixel((7, 7)) == (255, 255, 255)
    assert derived.getpixel((0, 0)) == (255, 0, 0)


def test_forty_megapixels_is_the_boundary() -> None:
    check_source_dimensions(8000, 5000)  # exactly 40,000,000
    with pytest.raises(DrawingNormalizationError) as raised:
        check_source_dimensions(8001, 5000)
    assert (raised.value.status_code, raised.value.code) == (422, "IMAGE_DIMENSIONS_EXCEEDED")
    with pytest.raises(DrawingNormalizationError) as degenerate:
        check_source_dimensions(0, 10)
    assert degenerate.value.code == "UPLOAD_CONTENT_MISMATCH"


def test_an_image_of_exactly_forty_megapixels_is_accepted_end_to_end() -> None:
    buffer = io.BytesIO()
    Image.new("1", (8000, 5000), 1).save(buffer, format="PNG")
    result = normalize_drawing(buffer.getvalue(), declared_media_type="image/png")
    assert result.width * result.height <= 2_000_000
    assert (result.source_width, result.source_height) == (8000, 5000)


def test_more_than_forty_megapixels_is_refused_before_any_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buffer = io.BytesIO()
    Image.new("1", (8001, 5000), 1).save(buffer, format="PNG")

    def fail_load(self: Image.Image) -> Any:
        raise AssertionError("pixels must not be decoded")

    monkeypatch.setattr(Image.Image, "load", fail_load)
    with pytest.raises(DrawingNormalizationError) as raised:
        normalize_drawing(buffer.getvalue(), declared_media_type="image/png")
    assert (raised.value.status_code, raised.value.code) == (422, "IMAGE_DIMENSIONS_EXCEEDED")


@pytest.mark.parametrize("side", [10_000, 100_000])
def test_a_decompression_bomb_maps_to_the_same_code(side: int) -> None:
    # 10,000 x 10,000 draws Pillow's warning, 100,000 x 100,000 its error (89M / 178M pixels).
    with pytest.raises(DrawingNormalizationError) as raised:
        normalize_drawing(_crafted_png(side, side), declared_media_type="image/png")
    assert (raised.value.status_code, raised.value.code) == (422, "IMAGE_DIMENSIONS_EXCEEDED")


def test_the_process_global_pixel_limit_is_never_written() -> None:
    before = Image.MAX_IMAGE_PIXELS
    normalize_drawing(_png(_shapes(32, 32)), declared_media_type="image/png")
    with pytest.raises(DrawingNormalizationError):
        normalize_drawing(_crafted_png(100_000, 100_000), declared_media_type="image/png")
    assert before == Image.MAX_IMAGE_PIXELS
    source = Path(drawing_module.__file__).read_text(encoding="utf-8")
    assert "MAX_IMAGE_PIXELS =" not in source and "MAX_IMAGE_PIXELS=" not in source


def test_undecodable_truncated_and_mismatched_content_is_rejected() -> None:
    for payload, declared in (
        (b"not an image at all", "image/png"),
        (_png(_shapes(64, 64))[:80], "image/png"),  # truncated inside the header chunks
        (_png(_shapes(64, 64)), "image/jpeg"),  # a PNG declared as JPEG
    ):
        with pytest.raises(DrawingNormalizationError) as raised:
            normalize_drawing(payload, declared_media_type=declared)
        assert (raised.value.status_code, raised.value.code) == (422, "UPLOAD_CONTENT_MISMATCH")


def test_a_png_over_five_megabytes_steps_down_the_ladder() -> None:
    source = _png(_noise(1500, 1300))  # incompressible: about 5.8 MB at 1.95 megapixels
    assert len(source) > 5_000_000
    result = normalize_drawing(source, declared_media_type="image/png")
    assert result.size_bytes <= 5_000_000
    assert result.width * result.height <= 1_200_000


def test_the_ladder_ends_in_the_documented_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(drawing_module, "DERIVED_MAX_BYTES", 10)
    with pytest.raises(DrawingNormalizationError) as raised:
        normalize_drawing(_png(_shapes(64, 64)), declared_media_type="image/png")
    assert (raised.value.status_code, raised.value.code) == (422, "IMAGE_DIMENSIONS_EXCEEDED")


def test_fit_within_never_exceeds_the_budget_or_grows() -> None:
    for width, height in ((3000, 2000), (2001, 1000), (1, 5_000_000), (1414, 1414)):
        new_width, new_height = fit_within(width, height, 2_000_000)
        assert new_width * new_height <= 2_000_000
        assert new_width <= width and new_height <= height and new_width >= 1 and new_height >= 1
    assert fit_within(800, 600, 2_000_000) == (800, 600)


# --------------------------------------------------------------------------- state matrix (D4)
def _run(state: str, job_state: str | None = None, retryable: bool = False) -> dict[str, Any]:
    return {"run_state": state, "job_state": job_state, "retryable": retryable}


@pytest.mark.parametrize(
    ("run", "attached", "slot"),
    [
        (_run("INPUT_PROCESSING"), [], "FIRST"),
        (_run("INPUT_PROCESSING", "QUEUED"), [], "FIRST"),
        (_run("SUBJECT_REVIEW", "SUCCEEDED"), ["parent/r/a/original"], "RETAKE"),
        # T-2c: the recoverable failure and a waiting transcript are reviewed in INPUT_REVIEW;
        # a failed analysis beside a transcript that is still PENDING stays in INPUT_PROCESSING.
        (_run("INPUT_PROCESSING", "FAILED", True), ["parent/r/a/original"], "RETAKE"),
        (_run("INPUT_REVIEW", "FAILED", True), ["parent/r/a/original"], "RETAKE"),
        (_run("INPUT_REVIEW", "SUCCEEDED"), ["parent/r/a/original"], "RETAKE"),
    ],
)
def test_the_slot_is_first_or_retake(run: dict[str, Any], attached: list[str], slot: str) -> None:
    assert SqlParentStoryRunRepository._artwork_slot(run, attached) == slot


@pytest.mark.parametrize(
    ("run", "attached"),
    [
        # a drawing is already attached and the analysis has not failed
        (_run("INPUT_PROCESSING", "QUEUED"), ["a"]),
        (_run("INPUT_PROCESSING", "RUNNING"), ["a"]),
        (_run("INPUT_PROCESSING", "AWAITING_RECONCILIATION"), ["a"]),
        # failed but not recoverable (terminal FAILED runs have another run_state anyway)
        (_run("INPUT_PROCESSING", "FAILED", False), ["a"]),
        # the retake is used up
        (_run("INPUT_PROCESSING", "FAILED", True), ["a", "b"]),
        (_run("INPUT_REVIEW", "FAILED", True), ["a", "b"]),
        (_run("SUBJECT_REVIEW", "SUCCEEDED"), ["a", "b"]),
        # no drawing yet cannot be reviewed
        (_run("SUBJECT_REVIEW", "SUCCEEDED"), []),
        (_run("INPUT_REVIEW"), []),
        # every later or terminal state
        (_run("PREPARATION_REVIEW"), ["a"]),
        (_run("SCRIPT_GENERATING"), ["a"]),
        (_run("SCRIPT_REVIEW"), ["a"]),
        (_run("FAILED"), ["a"]),
        (_run("COMPLETED"), ["a"]),
        (_run("DELETE_PENDING"), ["a"]),
        (_run("DELETED"), ["a"]),
        (_run("DELETED"), []),
    ],
)
def test_every_other_state_is_refused_with_the_given_code(
    run: dict[str, Any], attached: list[str]
) -> None:
    with pytest.raises(ParentStoryRunError) as raised:
        SqlParentStoryRunRepository._artwork_slot(run, attached, code="INVALID_STATE_TRANSITION")
    assert (raised.value.status_code, raised.value.code) == (409, "INVALID_STATE_TRANSITION")
    with pytest.raises(ParentStoryRunError) as legacy:
        SqlParentStoryRunRepository._artwork_slot(run, attached)
    assert legacy.value.code == "PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK"


# ----------------------------------------------------------------- copy-forward (R1 B10, C1)
RUN_INPUT_COLUMNS = {column.name for column in story_tables.run_inputs.columns}


def _previous_row() -> dict[str, Any]:
    return {name: f"previous-{name}" for name in RUN_INPUT_COLUMNS}


def test_the_next_input_carries_every_column_forward_except_the_drawing_ones() -> None:
    overrides = {name: f"new-{name}" for name in repository_module._DRAWING_INPUT_COLUMNS}
    values = repository_module._next_input_values(_previous_row(), **overrides)
    assert set(values) == RUN_INPUT_COLUMNS
    for name in RUN_INPUT_COLUMNS - repository_module._DRAWING_INPUT_COLUMNS:
        assert values[name] == f"previous-{name}", name
    for name in repository_module._DRAWING_INPUT_COLUMNS:
        assert values[name] == f"new-{name}", name


def test_a_drawing_column_without_a_value_is_an_error_not_a_silent_copy() -> None:
    with pytest.raises(RuntimeError):
        repository_module._next_input_values(_previous_row(), run_input_id="x")
    with pytest.raises(RuntimeError):
        repository_module._next_input_values(
            _previous_row(),
            **{name: "v" for name in repository_module._DRAWING_INPUT_COLUMNS},
            not_a_column="v",
        )


def test_a_future_column_is_copied_not_forgotten(monkeypatch: pytest.MonkeyPatch) -> None:
    """The trip-wire for any later run_inputs column: it moves forward by itself."""
    from sqlalchemy import Column, MetaData, String, Table

    clone = Table("run_inputs_clone", MetaData())
    for column in story_tables.run_inputs.columns:
        clone.append_column(column._copy())
    clone.append_column(Column("future_note", String(256)))
    monkeypatch.setattr(story_tables, "run_inputs", clone)
    previous = {**_previous_row(), "future_note": "note-1"}
    overrides = {name: "v" for name in repository_module._DRAWING_INPUT_COLUMNS}
    values = repository_module._next_input_values(previous, **overrides)
    assert values["future_note"] == "note-1"


def test_every_copy_forward_writer_names_all_run_input_columns() -> None:
    """Static check of each ``insert(run_inputs).values(...)`` in the copy-forward writers.

    T-2c C1: the writers that have a previous input row (the legacy drawing attach, the uploaded
    drawing attach and the idea writer) all go through ``_next_input_values``, so the voice columns
    cannot be dropped by a retake. ``create_run`` writes input revision 1 (no predecessor).
    """
    tree = ast.parse(Path(repository_module.__file__).read_text(encoding="utf-8"))
    checked: dict[str, int] = {}
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef) or function.name not in {
            "attach_artwork",
            "attach_uploaded_drawing",
            "_write_idea_input",
            "confirm_context",
        }:
            continue
        for call in ast.walk(function):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "values"
                and isinstance(call.func.value, ast.Call)
                and ast.unparse(call.func.value).endswith("insert(story_tables.run_inputs)")
            ):
                continue
            checked[function.name] = checked.get(function.name, 0) + 1
            keywords = {keyword.arg for keyword in call.keywords if keyword.arg is not None}
            splat = [keyword for keyword in call.keywords if keyword.arg is None]
            if splat:
                assert "_next_input_values" in ast.unparse(splat[0].value)
            else:
                assert keywords == RUN_INPUT_COLUMNS, function.name
    # T-12a: ``confirm_context`` writes the confirmed v2 input row of an explicit selection.
    assert checked == {
        "attach_artwork": 1,
        "attach_uploaded_drawing": 1,
        "_write_idea_input": 1,
        "confirm_context": 1,
    }
    writers = {
        function.name
        for function in ast.walk(tree)
        if isinstance(function, ast.FunctionDef)
        and "insert(story_tables.run_inputs)" in ast.unparse(function)
    }
    assert writers == {
        "create_run",
        "attach_artwork",
        "attach_uploaded_drawing",
        "_write_idea_input",
        "confirm_context",
    }


# ------------------------------------------------------------------------------ small helpers
def test_the_derived_key_shares_the_token_of_the_original() -> None:
    original = (
        "parent/6a5f1c2e-0000-4000-8000-000000000001/0123456789abcdef0123456789abcdef/original"
    )
    assert derived_asset_key(original) == (
        "parent/6a5f1c2e-0000-4000-8000-000000000001/0123456789abcdef0123456789abcdef/normalized.png"
    )


def test_the_fingerprint_binds_the_handle_and_the_expected_revision() -> None:
    base = drawing_attach_fingerprint("upl_a", None)
    assert base == drawing_attach_fingerprint("upl_a", None)
    assert base != drawing_attach_fingerprint("upl_b", None)
    assert base != drawing_attach_fingerprint("upl_a", 3)
    assert len(base) == 64


# ------------------------------------------------------------------- fixture analyzer discipline
def _request(sha: str = "a" * 64) -> DrawingAnalysisRequest:
    return DrawingAnalysisRequest(
        run_id="r",
        input_revision=2,
        derived_asset_ref="k",
        derived_sha256=sha,
        derived_size_bytes=9,
    )


def test_the_fixture_analyzer_answers_only_for_a_registered_hash() -> None:
    known = DrawingAnalysisResult("cat", ("ears",), 0.9)
    analyzer = FixtureDrawingAnalyzer({"a" * 64: known})
    assert analyzer.analyze(_request()) is known
    with pytest.raises(DrawingAnalysisFailure) as raised:
        analyzer.analyze(_request("b" * 64))
    assert raised.value.code == "DRAWING_ANALYSIS_UNAVAILABLE"
    assert len(analyzer.calls) == 2
    source = Path(runner_module.__file__).read_text(encoding="utf-8")
    assert "modal" not in source.lower()


def test_candidate_from_result_bounds_and_validates() -> None:
    candidate, subject, confidence = candidate_from_result(
        DrawingAnalysisResult("  cat  ", ("a", " b ", "c", "d", "e"), 0.5)
    )
    assert subject == "cat" and confidence == 0.5
    assert candidate["visible_features"] == ["a", "b", "c", "d"]
    assert candidate["adult_confirmation_required"] is True
    assert candidate["decision"] == "REVIEW_REQUIRED"
    for bad in (
        DrawingAnalysisResult("cat", (), 0.5),
        DrawingAnalysisResult("cat", ("a",), 1.5),
        DrawingAnalysisResult("cat", ("a",), float("nan")),
    ):
        with pytest.raises(DrawingAnalysisFailure):
            candidate_from_result(bad)


# ------------------------------------------------------------------------- the runner (fakes)
PRINCIPAL = VerifiedPrincipal(subject="parent-1", issuer="issuer", roles=frozenset())


class FakeRepository:
    """Records the runner's calls; ``scenario`` controls what the guards answer."""

    instances: list[FakeRepository] = []
    start_ok = True
    recover_ok = True
    understanding_error: ParentStoryRunError | None = None
    input_revision = 2

    def __init__(self, session: Any) -> None:
        self.session = session
        self.calls: list[tuple[str, dict[str, Any]]] = []
        FakeRepository.instances.append(self)

    def start_drawing_analysis(self, **kwargs: Any) -> bool:
        self.calls.append(("start", kwargs))
        return self.start_ok

    def read_subject_rerun_hint(self, **kwargs: Any) -> str | None:
        return None  # T-2d: no rerun is pending in these scenarios

    def read_current_input(self, **kwargs: Any) -> Any:
        return SimpleNamespace(
            input_revision=self.input_revision,
            derived_asset_ref="parent/r/t/normalized.png",
            derived_sha256="a" * 64,
            derived_size_bytes=10,
        )

    def record_understanding(self, **kwargs: Any) -> int:
        self.calls.append(("understanding", kwargs))
        if self.understanding_error is not None:
            raise self.understanding_error
        return 1

    def fail_drawing_analysis_recoverable(self, **kwargs: Any) -> bool:
        self.calls.append(("recoverable", kwargs))
        return self.recover_ok

    def fail_drawing_analysis(self, **kwargs: Any) -> None:
        self.calls.append(("unknown", kwargs))


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_repository(monkeypatch: pytest.MonkeyPatch) -> type[FakeRepository]:
    FakeRepository.instances = []
    FakeRepository.start_ok = True
    FakeRepository.recover_ok = True
    FakeRepository.understanding_error = None
    FakeRepository.input_revision = 2
    monkeypatch.setattr(runner_module, "SqlParentStoryRunRepository", FakeRepository)
    return FakeRepository


class _Analyzer:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls = 0

    def analyze(self, request: DrawingAnalysisRequest) -> DrawingAnalysisResult:
        self.calls += 1
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome  # type: ignore[no-any-return]


def _execute(analyzer: _Analyzer) -> tuple[FakeRepository, FakeSession]:
    sessions: list[FakeSession] = []

    def factory() -> FakeSession:
        sessions.append(FakeSession())
        return sessions[-1]

    ParentInputJobRunner(factory, analyzer).run(PRINCIPAL, "run-1", 2)  # type: ignore[arg-type]
    assert len(sessions) == 1  # the runner opens its own session, one per run
    return FakeRepository.instances[-1], sessions[-1]


def test_a_result_is_recorded_for_the_input_it_was_started_for(
    fake_repository: type[FakeRepository],
) -> None:
    repo, session = _execute(_Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8)))
    names = [name for name, _ in repo.calls]
    assert names == ["start", "understanding"]
    kwargs = repo.calls[1][1]
    assert kwargs["expected_input_revision"] == 2
    assert kwargs["candidate_subject"] == "cat"
    assert kwargs["result_snapshot"] == {"result": kwargs["result_snapshot"]["result"]}
    assert session.closed is True


def test_a_topic_mismatch_is_a_warning_beside_the_candidate(
    fake_repository: type[FakeRepository],
) -> None:
    repo, _ = _execute(
        _Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8, topic_compatible=False))
    )
    snapshot = repo.calls[1][1]["result_snapshot"]
    assert snapshot["warnings"] == [{"code": "TOPIC_MISMATCH"}]
    assert "warnings" not in snapshot["result"]


def test_more_than_one_child_is_the_recoverable_multi_child_failure(
    fake_repository: type[FakeRepository],
) -> None:
    repo, _ = _execute(_Analyzer(DrawingAnalysisResult("cats", ("ears",), 0.8, child_count=2)))
    names = [name for name, _ in repo.calls]
    assert names == ["start", "recoverable"]
    assert repo.calls[1][1]["error_code"] == "MULTI_CHILD_NOT_SUPPORTED"
    assert repo.calls[1][1]["expected_input_revision"] == 2


def test_an_unknown_input_and_an_analyzer_defect_are_recoverable_failures(
    fake_repository: type[FakeRepository],
) -> None:
    repo, _ = _execute(_Analyzer(DrawingAnalysisFailure("DRAWING_ANALYSIS_UNAVAILABLE")))
    assert repo.calls[-1][0] == "recoverable"
    assert repo.calls[-1][1]["error_code"] == "DRAWING_ANALYSIS_UNAVAILABLE"
    repo, _ = _execute(_Analyzer(RuntimeError("boom")))
    assert repo.calls[-1][0] == "recoverable"
    assert repo.calls[-1][1]["error_code"] == "DRAWING_ANALYSIS_FAILED"


def test_an_unknown_outcome_goes_to_reconciliation_not_to_a_retake(
    fake_repository: type[FakeRepository],
) -> None:
    repo, _ = _execute(_Analyzer(DrawingAnalysisOutcomeUnknown()))
    assert repo.calls[-1][0] == "unknown"
    assert repo.calls[-1][1]["outcome_unknown"] is True
    # T-2d-fix: the write is fenced by the input revision it was started for
    assert type(repo.calls[-1][1]["expected_input_revision"]) is int


def test_work_that_is_no_longer_current_is_skipped_without_calling_the_analyzer(
    fake_repository: type[FakeRepository],
) -> None:
    fake_repository.start_ok = False  # cancelled, purged, or the input was replaced
    analyzer = _Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8))
    repo, session = _execute(analyzer)
    assert [name for name, _ in repo.calls] == ["start"]
    assert analyzer.calls == 0
    assert session.closed is True
    # T-2c: a later input revision (an idea or audio copies the drawing forward) is still current:
    # the repository guards by drawing, so the runner analyses and records the result.
    fake_repository.start_ok = True
    fake_repository.input_revision = 3
    analyzer = _Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8))
    repo, _ = _execute(analyzer)
    assert [name for name, _ in repo.calls] == ["start", "understanding"]
    assert analyzer.calls == 1
    assert repo.calls[-1][1]["expected_input_revision"] == 2


def test_a_stale_result_is_discarded_and_nothing_escapes_the_task(
    fake_repository: type[FakeRepository],
) -> None:
    fake_repository.understanding_error = ParentStoryRunError(409, "PARENT_STORY_INPUT_REPLACED")
    repo, session = _execute(_Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8)))
    assert [name for name, _ in repo.calls] == ["start", "understanding"]
    assert session.closed is True


def test_a_store_outage_does_not_escape_the_background_task(
    fake_repository: type[FakeRepository],
) -> None:
    fake_repository.understanding_error = ParentStoryRunError(
        503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"
    )
    _execute(_Analyzer(DrawingAnalysisResult("cat", ("ears",), 0.8)))
