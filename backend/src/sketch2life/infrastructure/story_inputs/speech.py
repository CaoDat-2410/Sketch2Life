"""Run the speech transcription after the 202 response (goal v3 T-2c, SRS l.731, OD-13).

``ParentSpeechJobRunner.run`` is scheduled through ``BackgroundTasks`` by ``POST .../idea`` when
audio was submitted and a transcriber is composed (``app.state.speech_transcriber``). With none
composed the transcript stays ``PENDING`` and the run waits (the adult can cancel it). FastAPI
closes the request's dependencies before background tasks run, so the runner opens its own session
and closes it.

Outcomes, each written under the run lock and guarded by the transcript row it was started for (a
transcript superseded by a newer audio or a purged run is discarded and changes nothing):

* a text: ``NEEDS_CONFIRMATION`` (the hash covers the raw text); the run state is settled, so the
  adult sees ``INPUT_REVIEW`` once the drawing is understood (T2C-D6);
* an empty text, a text over 20,000 characters, ``SpeechTranscriptionFailure`` or any other
  error: ``FAILED`` with a stable code; the adult can type the idea as a correction.

ASR text is untrusted and is not safety-screened here (FR-AI-12, l.578: the policy does not exist,
recorded debt). It is never logged and reaches only the adult's transcript read and, after the
adult confirmed that exact revision, the story input.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    ASR_FAILED,
    MAX_RAW_TRANSCRIPT_CHARS,
    MAX_SEGMENT_TIMING_ITEMS,
    TRANSCRIPT_EMPTY,
    TRANSCRIPT_TOO_LONG,
    SpeechTranscriberPort,
    SpeechTranscriptionFailure,
    SpeechTranscriptionResult,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_LOGGER = logging.getLogger("sketch2life.api")


def _bounded_timing(result: SpeechTranscriptionResult) -> list[dict[str, int]] | None:
    """The segment timing when it is a short list of non-negative ``start_ms``/``end_ms``."""
    timing = result.segment_timing
    if not timing or len(timing) > MAX_SEGMENT_TIMING_ITEMS:
        return None
    items: list[dict[str, int]] = []
    for item in timing:
        start, end = item.get("start_ms"), item.get("end_ms")
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start <= end <= 24 * 3600 * 1000
        ):
            return None
        items.append({"start_ms": start, "end_ms": end})
    return items


class ParentSpeechJobRunner:
    def __init__(
        self, session_factory: Callable[[], Session], transcriber: SpeechTranscriberPort
    ) -> None:
        self._session_factory = session_factory
        self._transcriber = transcriber

    def run(self, principal: VerifiedPrincipal, run_id: str, transcript_revision_id: str) -> None:
        """Never raises: a background task has no caller to report to; failures are recorded."""
        session = self._session_factory()
        try:
            self._run(session, principal, run_id, transcript_revision_id)
        except ParentStoryRunError as exc:
            # Stale or purged work is discarded; a store outage leaves the transcript PENDING.
            _LOGGER.info("parent_speech_job_discarded code=%s", exc.code)
        except Exception as exc:  # noqa: BLE001 - nothing may escape a background task
            _LOGGER.warning("parent_speech_job_error type=%s", type(exc).__name__)
        finally:
            session.close()

    def _run(
        self,
        session: Session,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
    ) -> None:
        repository = SqlParentStoryRunRepository(session)
        request = repository.read_pending_transcription(
            principal=principal, run_id=run_id, transcript_revision_id=transcript_revision_id
        )
        if request is None:
            return
        try:
            result = self._transcriber.transcribe(request)
        except SpeechTranscriptionFailure as failure:
            self._fail(repository, principal, run_id, transcript_revision_id, failure.code)
            return
        except Exception:  # noqa: BLE001 - a transcriber defect is a recoverable failure
            self._fail(repository, principal, run_id, transcript_revision_id, ASR_FAILED)
            return
        text = result.text.strip() if isinstance(result.text, str) else ""
        if not text:
            self._fail(repository, principal, run_id, transcript_revision_id, TRANSCRIPT_EMPTY)
            return
        if len(text) > MAX_RAW_TRANSCRIPT_CHARS:
            self._fail(repository, principal, run_id, transcript_revision_id, TRANSCRIPT_TOO_LONG)
            return
        repository.complete_transcript(
            principal=principal,
            run_id=run_id,
            transcript_revision_id=transcript_revision_id,
            text=text,
            language=result.language,
            model_revision=result.model_revision,
            config_hash=result.config_hash,
            asr_profile_ref=result.asr_profile_ref,
            segment_timing=_bounded_timing(result),
        )

    @staticmethod
    def _fail(
        repository: SqlParentStoryRunRepository,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        code: str,
    ) -> None:
        repository.fail_transcript(
            principal=principal,
            run_id=run_id,
            transcript_revision_id=transcript_revision_id,
            error_code=code,
        )


__all__ = ["ParentSpeechJobRunner"]
