"""FEAT-066 T-2c: the input state machine, the request model and the speech runner (offline).

The behaviour against PostgreSQL and S3Mock is in
``tests/integration/test_parent_story_idea_postgres.py``; this module holds the pure parts: the
settle assertion table (T2C-D6), the idea source rule, the request and response models, the
fingerprint, the fixture transcriber discipline and the background runner with fakes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

import sketch2life.infrastructure.persistence.parent_story_repository as repository_module
import sketch2life.infrastructure.story_inputs.speech as speech_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    SpeechTranscriptionFailure,
    SpeechTranscriptionRequest,
    SpeechTranscriptionResult,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.contracts.schemas.parent_story_inputs import (
    AddRunIdeaRequestV1,
    ConfirmTranscriptRequestV1,
    ParentRunTranscriptV1,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    idea_fingerprint,
    idea_source_for,
    settle_input_state,
)
from sketch2life.infrastructure.story_inputs.fixtures import FixtureSpeechTranscriber
from sketch2life.infrastructure.story_inputs.speech import ParentSpeechJobRunner

IP, IR, SR = "INPUT_PROCESSING", "INPUT_REVIEW", "SUBJECT_REVIEW"


def settle(
    *,
    drawing: bool = True,
    understood: bool = False,
    vlm: str | None = "QUEUED",
    transcript: str | None = None,
) -> str:
    return settle_input_state(
        has_drawing=drawing, understood=understood, vlm_job_state=vlm, transcript_state=transcript
    )


# ------------------------------------------------------------------ settle assertion table (D6)
@pytest.mark.parametrize(
    ("case", "kwargs", "expected"),
    [
        # (A) text only: the VLM result moves the run to SUBJECT_REVIEW
        ("A-vlm-running", {"vlm": "RUNNING"}, IP),
        ("A-vlm-ok", {"understood": True, "vlm": "SUCCEEDED"}, SR),
        # (B) voice: ASR ok first with the VLM still running stays in INPUT_PROCESSING
        ("B-asr-ok-vlm-running", {"vlm": "RUNNING", "transcript": "NEEDS_CONFIRMATION"}, IP),
        (
            "B-vlm-ok",
            {"understood": True, "vlm": "SUCCEEDED", "transcript": "NEEDS_CONFIRMATION"},
            IR,
        ),
        ("B-confirmed", {"understood": True, "vlm": "SUCCEEDED", "transcript": "CONFIRMED"}, SR),
        # (C) VLM ok first, the ASR still running
        ("C-asr-running", {"understood": True, "vlm": "SUCCEEDED", "transcript": "PENDING"}, IP),
        (
            "C-asr-ok",
            {"understood": True, "vlm": "SUCCEEDED", "transcript": "NEEDS_CONFIRMATION"},
            IR,
        ),
        # (D) ASR failed, VLM ok: the adult types the idea (correction), then confirms
        ("D-asr-failed", {"understood": True, "vlm": "SUCCEEDED", "transcript": "FAILED"}, IR),
        (
            "D-corrected-unconfirmed",
            {"understood": True, "vlm": "SUCCEEDED", "transcript": "NEEDS_CONFIRMATION"},
            IR,
        ),
        (
            "D-corrected-confirmed",
            {"understood": True, "vlm": "SUCCEEDED", "transcript": "CONFIRMED"},
            SR,
        ),
        # (E) a text-only idea in SUBJECT_REVIEW leaves the state (no voice)
        ("E-text-only", {"understood": True, "vlm": "SUCCEEDED", "transcript": None}, SR),
        # (F) audio in SUBJECT_REVIEW: the new transcript is PENDING
        ("F-audio", {"understood": True, "vlm": "SUCCEEDED", "transcript": "PENDING"}, IP),
        # (G) a correction after a confirmation returns the run to the review
        (
            "G-correct-after-confirm",
            {"understood": True, "vlm": "SUCCEEDED", "transcript": "NEEDS_CONFIRMATION"},
            IR,
        ),
        # recoverable VLM failure (T-2b moves from INPUT_PROCESSING/FAILED to INPUT_REVIEW)
        ("vlm-failed", {"vlm": "FAILED"}, IR),
        ("vlm-failed-asr-pending", {"vlm": "FAILED", "transcript": "PENDING"}, IP),
        ("vlm-failed-asr-ok", {"vlm": "FAILED", "transcript": "NEEDS_CONFIRMATION"}, IR),
        # no drawing yet: the adult may still add the idea, the state does not move
        ("no-drawing", {"drawing": False, "vlm": None}, IP),
        (
            "no-drawing-asr-ok",
            {"drawing": False, "vlm": None, "transcript": "NEEDS_CONFIRMATION"},
            IP,
        ),
        ("no-drawing-confirmed", {"drawing": False, "vlm": None, "transcript": "CONFIRMED"}, IP),
        # an unknown outcome waits for reconciliation, never reviews
        ("vlm-unknown", {"vlm": "AWAITING_RECONCILIATION"}, IP),
        ("vlm-unset", {"vlm": None}, IP),
    ],
)
def test_the_settle_table(case: str, kwargs: dict[str, Any], expected: str) -> None:
    assert settle(**kwargs) == expected, case


def test_a_retake_hides_the_old_understanding_so_the_new_drawing_waits_for_its_own_vlm() -> None:
    # (H) after a retake the drawing is not understood again and its job is QUEUED; the confirmed
    # transcript (copied forward) does not move the run out of INPUT_PROCESSING.
    assert settle(understood=False, vlm="QUEUED", transcript="CONFIRMED") == IP
    assert settle(understood=True, vlm="SUCCEEDED", transcript="CONFIRMED") == SR


def test_the_rules_are_total_over_every_combination() -> None:
    states = {IP, IR, SR}
    for drawing in (True, False):
        for understood in (True, False):
            for vlm in (
                None,
                "QUEUED",
                "RUNNING",
                "SUCCEEDED",
                "FAILED",
                "AWAITING_RECONCILIATION",
            ):
                for transcript in (None, "PENDING", "NEEDS_CONFIRMATION", "CONFIRMED", "FAILED"):
                    result = settle(
                        drawing=drawing, understood=understood, vlm=vlm, transcript=transcript
                    )
                    assert result in states
                    if not drawing:
                        assert result == IP
                    if transcript == "PENDING":
                        assert result == IP


# ------------------------------------------------------------------------------ small rules
@pytest.mark.parametrize(
    ("typed", "voice", "source"),
    [
        (None, None, None),
        ("", None, None),
        ("a cat", None, "TEXT"),
        (None, "parent/r/t/original", "VOICE"),
        ("a cat", "parent/r/t/original", "TEXT_AND_VOICE"),
    ],
)
def test_the_idea_source_follows_the_text_and_the_voice(
    typed: str | None, voice: str | None, source: str | None
) -> None:
    assert idea_source_for(typed, voice) == source


def test_the_effective_text_and_the_combined_idea() -> None:
    corrected = {"adult_corrected_text": "fixed", "raw_transcript": "raw"}
    raw_only = {"adult_corrected_text": None, "raw_transcript": "raw"}
    failed = {"adult_corrected_text": None, "raw_transcript": None}
    assert repository_module._effective_transcript_text(corrected) == "fixed"
    assert repository_module._effective_transcript_text(raw_only) == "raw"
    assert repository_module._effective_transcript_text(failed) is None
    assert repository_module._combined_idea(None, "voice") == "voice"
    assert repository_module._combined_idea("typed", None) == "typed"
    assert repository_module._combined_idea("typed", "voice") == "typed voice"
    assert repository_module._combined_idea(None, None) == ""
    digest = repository_module._text_sha256("tiếng Việt")
    assert digest == hashlib.sha256("tiếng Việt".encode()).hexdigest()


def test_the_idea_fingerprint_binds_every_field() -> None:
    base = idea_fingerprint(3, "a cat", None, None)
    assert base == idea_fingerprint(3, "a cat", None, None) and len(base) == 64
    assert base != idea_fingerprint(4, "a cat", None, None)
    assert base != idea_fingerprint(3, "a dog", None, None)
    assert base != idea_fingerprint(3, "a cat", "upl_x", None)
    assert idea_fingerprint(3, None, None, (1, "x")) != idea_fingerprint(3, None, None, (2, "x"))
    assert idea_fingerprint(3, None, None, (1, "x")) != idea_fingerprint(3, None, None, (1, "y"))
    assert idea_fingerprint(3, None, None, (1, "x")) != base


# ------------------------------------------------------------------------------ request models
HANDLE = "upl_11111111-1111-4111-8111-111111111111"


def _idea(**fields: Any) -> AddRunIdeaRequestV1:
    return AddRunIdeaRequestV1.model_validate({"expected_run_revision": 2, **fields})


def test_a_text_an_audio_or_both_are_one_valid_group() -> None:
    assert _idea(text="a cat").text == "a cat"
    assert _idea(audio_ref=HANDLE).audio_ref == HANDLE
    both = _idea(text="a cat", audio_ref=HANDLE)
    assert both.text == "a cat" and both.audio_ref == HANDLE
    assert _idea(text="  padded  ").text == "padded"


def test_a_correction_is_its_own_group() -> None:
    request = _idea(transcript_correction={"base_revision": 1, "text": "  fixed  "})
    assert request.transcript_correction is not None
    assert request.transcript_correction.text == "fixed"


@pytest.mark.parametrize(
    "fields",
    [
        {},  # none
        {"text": "a", "transcript_correction": {"base_revision": 1, "text": "b"}},  # mixed
        {"audio_ref": HANDLE, "transcript_correction": {"base_revision": 1, "text": "b"}},
        {"text": ""},
        {"text": "   "},
        {"text": "x" * 501},
        {"text": 5},
        {"audio_ref": "upl_short"},
        {"audio_ref": "parent/run/original"},
        {"audio_ref": "s3://bucket/key"},
        {"text": "a", "owner": "x"},  # unknown field
        {"text": "a", "bucket": "b"},
        {"transcript_correction": {"base_revision": 0, "text": "b"}},
        {"transcript_correction": {"base_revision": 1, "text": "   "}},
        {"transcript_correction": {"base_revision": 1, "text": "x" * 501}},
        {"transcript_correction": {"base_revision": 1, "text": "b", "extra": 1}},
    ],
)
def test_an_invalid_idea_request_is_refused(fields: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _idea(**fields)


def test_the_expected_run_revision_is_required_and_positive() -> None:
    for body in ({"text": "a"}, {"expected_run_revision": 0, "text": "a"}):
        with pytest.raises(ValidationError):
            AddRunIdeaRequestV1.model_validate(body)


def test_a_500_character_text_is_the_limit() -> None:
    assert len(_idea(text="y" * 500).text or "") == 500


def test_the_confirmation_request_is_exact() -> None:
    good = {"expected_transcript_revision": 2, "transcript_sha256": "a" * 64, "confirmed": True}
    assert ConfirmTranscriptRequestV1.model_validate(good).expected_transcript_revision == 2
    for change in (
        {"confirmed": False},
        {"confirmed": "true"},
        {"transcript_sha256": "A" * 64},
        {"transcript_sha256": "a" * 63},
        {"expected_transcript_revision": 0},
        {"extra": 1},
    ):
        with pytest.raises(ValidationError):
            ConfirmTranscriptRequestV1.model_validate({**good, **change})
    with pytest.raises(ValidationError):
        ConfirmTranscriptRequestV1.model_validate(
            {k: v for k, v in good.items() if k != "confirmed"}
        )


def test_the_transcript_response_has_no_job_and_no_storage_field() -> None:
    fields = set(ParentRunTranscriptV1.model_fields)
    assert "job" not in fields
    assert not {"asset_ref", "audio_ref", "bucket", "key", "voice_asset_ref"} & fields


# --------------------------------------------------------------------------- fixture transcriber
def _request(sha: str = "a" * 64) -> SpeechTranscriptionRequest:
    return SpeechTranscriptionRequest(
        run_id="r",
        transcript_revision_id="t",
        audio_asset_ref="parent/r/x/original",
        audio_sha256=sha,
        media_type="audio/wav",
        duration_ms=1000,
    )


def test_the_fixture_transcriber_answers_only_for_a_registered_hash() -> None:
    transcriber = FixtureSpeechTranscriber({"a" * 64: "xin chào"})
    result = transcriber.transcribe(_request())
    assert result.text == "xin chào" and result.language == "vi"
    full = SpeechTranscriptionResult(text="đầy đủ", language="vi", model_revision="m1")
    transcriber.register("b" * 64, full)
    assert transcriber.transcribe(_request("b" * 64)) is full
    with pytest.raises(SpeechTranscriptionFailure) as raised:
        transcriber.transcribe(_request("c" * 64))
    assert raised.value.code == "ASR_UNAVAILABLE"
    assert len(transcriber.calls) == 3


def test_no_provider_or_network_name_appears_in_the_speech_modules() -> None:
    import ast

    from sketch2life.application.ports import parent_story_inputs as ports
    from sketch2life.infrastructure.story_inputs import fixtures, idea

    banned = ("modal", "openai", "whisper", "requests", "httpx", "boto3", "botocore", "urllib")
    for module in (speech_module, idea, fixtures, ports):
        tree = ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))
        imported = {
            name.split(".")[0]
            for node in ast.walk(tree)
            for name in (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
        }
        assert not imported & set(banned), (module.__name__, imported & set(banned))


# ---------------------------------------------------------------------- the runner (with fakes)
PRINCIPAL = VerifiedPrincipal(subject="parent-1", issuer="issuer", roles=frozenset())


class FakeRepository:
    instances: list[FakeRepository] = []
    request: SpeechTranscriptionRequest | None = _request()
    complete_error: ParentStoryRunError | None = None

    def __init__(self, session: Any) -> None:
        self.session = session
        self.calls: list[tuple[str, dict[str, Any]]] = []
        FakeRepository.instances.append(self)

    def read_pending_transcription(self, **kwargs: Any) -> SpeechTranscriptionRequest | None:
        self.calls.append(("read", kwargs))
        return self.request

    def complete_transcript(self, **kwargs: Any) -> bool:
        self.calls.append(("complete", kwargs))
        if self.complete_error is not None:
            raise self.complete_error
        return True

    def fail_transcript(self, **kwargs: Any) -> bool:
        self.calls.append(("fail", kwargs))
        return True


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_repository(monkeypatch: pytest.MonkeyPatch) -> type[FakeRepository]:
    FakeRepository.instances = []
    FakeRepository.request = _request()
    FakeRepository.complete_error = None
    monkeypatch.setattr(speech_module, "SqlParentStoryRunRepository", FakeRepository)
    return FakeRepository


class _Transcriber:
    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls = 0

    def transcribe(self, request: SpeechTranscriptionRequest) -> SpeechTranscriptionResult:
        self.calls += 1
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome  # type: ignore[no-any-return]


def _execute(transcriber: _Transcriber) -> tuple[FakeRepository, FakeSession]:
    sessions: list[FakeSession] = []

    def factory() -> FakeSession:
        sessions.append(FakeSession())
        return sessions[-1]

    ParentSpeechJobRunner(factory, transcriber).run(PRINCIPAL, "run-1", "t-1")  # type: ignore[arg-type]
    assert len(sessions) == 1  # the runner opens its own session, one per run
    return FakeRepository.instances[-1], sessions[-1]


def test_a_text_completes_the_transcript(fake_repository: type[FakeRepository]) -> None:
    repo, session = _execute(_Transcriber(SpeechTranscriptionResult(text="  xin chào  ")))
    assert [name for name, _ in repo.calls] == ["read", "complete"]
    assert repo.calls[1][1]["text"] == "xin chào"
    assert repo.calls[1][1]["transcript_revision_id"] == "t-1"
    assert session.closed is True


@pytest.mark.parametrize(
    ("outcome", "code"),
    [
        (SpeechTranscriptionFailure("ASR_UNAVAILABLE"), "ASR_UNAVAILABLE"),
        (RuntimeError("provider exploded with the audio text"), "ASR_FAILED"),
        (SpeechTranscriptionResult(text="   "), "TRANSCRIPT_EMPTY"),
        (SpeechTranscriptionResult(text="x" * 20_001), "TRANSCRIPT_TOO_LONG"),
    ],
)
def test_a_failure_is_recorded_with_a_stable_code(
    fake_repository: type[FakeRepository], outcome: Any, code: str
) -> None:
    repo, session = _execute(_Transcriber(outcome))
    assert [name for name, _ in repo.calls] == ["read", "fail"]
    assert repo.calls[1][1]["error_code"] == code
    assert session.closed is True


def test_stale_work_is_skipped_without_calling_the_transcriber(
    fake_repository: type[FakeRepository],
) -> None:
    fake_repository.request = None  # superseded, purged or already done
    transcriber = _Transcriber(SpeechTranscriptionResult(text="x"))
    repo, session = _execute(transcriber)
    assert [name for name, _ in repo.calls] == ["read"]
    assert transcriber.calls == 0 and session.closed is True


def test_nothing_escapes_the_background_task(
    fake_repository: type[FakeRepository], caplog: pytest.LogCaptureFixture
) -> None:
    fake_repository.complete_error = ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
    _execute(_Transcriber(SpeechTranscriptionResult(text="a secret child sentence")))
    assert "secret child sentence" not in caplog.text


def test_segment_timing_is_kept_only_when_it_is_well_formed() -> None:
    def result(timing: Any) -> SpeechTranscriptionResult:
        return SpeechTranscriptionResult(text="x", segment_timing=timing)

    good = result(({"start_ms": 0, "end_ms": 500}, {"start_ms": 500, "end_ms": 900}))
    assert speech_module._bounded_timing(good) == [
        {"start_ms": 0, "end_ms": 500},
        {"start_ms": 500, "end_ms": 900},
    ]
    assert speech_module._bounded_timing(result(None)) is None
    assert speech_module._bounded_timing(result(())) is None
    assert speech_module._bounded_timing(result(({"start_ms": 5, "end_ms": 1},))) is None
    assert speech_module._bounded_timing(result(({"start_ms": -1, "end_ms": 1},))) is None
    assert speech_module._bounded_timing(result(({"start_ms": "0", "end_ms": 1},))) is None
    assert speech_module._bounded_timing(result(({"start_ms": 0},))) is None
    too_many = tuple({"start_ms": 0, "end_ms": 1} for _ in range(501))
    assert speech_module._bounded_timing(result(too_many)) is None


def test_the_runner_namespace_has_no_fixture_transcriber_default() -> None:
    namespace = SimpleNamespace(**vars(speech_module))
    assert not hasattr(namespace, "FixtureSpeechTranscriber")
