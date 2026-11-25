"""Run the drawing analysis after the 202 response (goal v3 T-2b, SRS l.394, OD-13).

``ParentInputJobRunner.run`` is scheduled through ``BackgroundTasks``. FastAPI closes the request's
dependencies (including its database session) before background tasks run, so the runner opens its
own session from the session factory and closes it. Every write is guarded by the input revision it
was started for: a result for a drawing that a retake replaced, or for a run that was cancelled, is
discarded and changes nothing.

Outcomes:

* result with ``child_count > 1``: the recoverable failure ``MULTI_CHILD_NOT_SUPPORTED`` (l.871),
  ``job_state FAILED``, the run in ``INPUT_REVIEW`` (T-2c settle rule), the active slot kept, one
  retake allowed (T2B-D4);
* any other result: ``record_understanding`` (the run moves to ``SUBJECT_REVIEW``, or stays in
  ``INPUT_PROCESSING``/``INPUT_REVIEW`` while a transcript waits); a topic mismatch is stored as a
  warning beside the result;
* ``DrawingAnalysisFailure`` or an unexpected error: the same recoverable failure with its code;
* ``DrawingAnalysisOutcomeUnknown``: ``fail_drawing_analysis(outcome_unknown=True)``
  (``AWAITING_RECONCILIATION``, never a retake).

Every failure write is a compare-and-set (T-2d-fix): a run the reaper already settled, a replaced
drawing or a job that is no longer in flight answers 409 and the work is discarded.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from math import isfinite
from typing import Any

from sqlalchemy.orm import Session

from sketch2life.application.parent_subject_roles import normalize_worker_candidate
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    DRAWING_ANALYSIS_FAILED,
    MAX_VISIBLE_FEATURES,
    MULTI_CHILD_NOT_SUPPORTED,
    DrawingAnalysisFailure,
    DrawingAnalysisOutcomeUnknown,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
    DrawingAnalyzerPort,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import RunActor
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    job_side_repository,
)

_LOGGER = logging.getLogger("sketch2life.api")
_SUBJECT_MAX = 160


def candidate_from_result(result: DrawingAnalysisResult) -> tuple[dict[str, Any], str, float]:
    """The stored candidate body, the subject label and the confidence (same shape as legacy)."""
    subject = result.subject.strip()[:_SUBJECT_MAX]
    features = [
        value.strip()[:_SUBJECT_MAX]
        for value in result.visible_features[:MAX_VISIBLE_FEATURES]
        if isinstance(value, str) and value.strip()
    ]
    if (
        not features
        or isinstance(result.confidence, bool)
        or not isfinite(float(result.confidence))
        or not 0 <= float(result.confidence) <= 1
    ):
        raise DrawingAnalysisFailure(DRAWING_ANALYSIS_FAILED)
    candidate = {
        "candidate_subject": subject or None,
        "visible_features": features,
        "confidence": float(result.confidence),
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
    raw = result.raw_candidate
    if isinstance(raw, dict):
        # FEAT-093 M1: keep the main and secondary subjects (with boxes) the worker found; the
        # client only ever sees ``present_candidate`` (labels and suggested roles, no boxes).
        detailed = normalize_worker_candidate(raw)
        for key in ("understanding_schema", "main_subject", "secondary_subjects"):
            if key in detailed:
                candidate[key] = detailed[key]
    return candidate, subject or "UNCONFIRMED", float(result.confidence)


class ParentInputJobRunner:
    def __init__(
        self, session_factory: Callable[[], Session], analyzer: DrawingAnalyzerPort
    ) -> None:
        self._session_factory = session_factory
        self._analyzer = analyzer

    def run(
        self,
        principal: VerifiedPrincipal,
        run_id: str,
        input_revision: int,
        actor: RunActor | None = None,
        organization_id: str | None = None,
    ) -> None:
        """Never raises: a background task has no caller to report to; failures are recorded.

        For a Teacher run ``actor`` and the ``organization_id`` the route saw select the job-side
        repository (T-4b3a D6); a Parent run passes neither and is the unchanged Parent path."""
        session = self._session_factory()
        try:
            self._run(session, principal, run_id, input_revision, actor, organization_id)
        except ParentStoryRunError as exc:
            # Stale or purged work is discarded; a store outage leaves the run QUEUED/RUNNING.
            _LOGGER.info("parent_input_job_discarded code=%s", exc.code)
        except Exception as exc:  # noqa: BLE001 - nothing may escape a background task
            _LOGGER.warning("parent_input_job_error type=%s", type(exc).__name__)
        finally:
            session.close()

    def _run(
        self,
        session: Session,
        principal: VerifiedPrincipal,
        run_id: str,
        input_revision: int,
        actor: RunActor | None,
        organization_id: str | None,
    ) -> None:
        repository = (
            SqlParentStoryRunRepository(session)
            if actor is None
            else job_side_repository(session, actor, organization_id)
        )
        if not repository.start_drawing_analysis(
            principal=principal, run_id=run_id, expected_input_revision=input_revision
        ):
            return
        # The input revision may have moved on (an idea or audio revision copies the drawing
        # forward, T-2c); ``start_drawing_analysis`` already checked that the drawing is the same.
        current = repository.read_current_input(principal=principal, run_id=run_id)
        if (
            current.derived_asset_ref is None
            or current.derived_sha256 is None
            or current.derived_size_bytes is None
        ):
            return
        request = DrawingAnalysisRequest(
            run_id=run_id,
            input_revision=current.input_revision,
            derived_asset_ref=current.derived_asset_ref,
            derived_sha256=current.derived_sha256,
            derived_size_bytes=current.derived_size_bytes,
            # T-2d: after a subject edit the same drawing is analyzed again with the adult's
            # subject as data (SRS l.394, l.1413); ``None`` for a first analysis or a retake.
            subject_hint=repository.read_subject_rerun_hint(principal=principal, run_id=run_id),
        )
        try:
            result = self._analyzer.analyze(request)
            if result.child_count > 1:
                raise DrawingAnalysisFailure(MULTI_CHILD_NOT_SUPPORTED)
            candidate, subject, confidence = candidate_from_result(result)
        except DrawingAnalysisOutcomeUnknown:
            repository.fail_drawing_analysis(
                principal=principal,
                run_id=run_id,
                error_code="DRAWING_OUTCOME_UNKNOWN",
                outcome_unknown=True,
                expected_input_revision=input_revision,
            )
            return
        except DrawingAnalysisFailure as failure:
            repository.fail_drawing_analysis_recoverable(
                principal=principal,
                run_id=run_id,
                error_code=failure.code,
                expected_input_revision=input_revision,
            )
            return
        except Exception:  # noqa: BLE001 - an analyzer defect is a recoverable failure
            repository.fail_drawing_analysis_recoverable(
                principal=principal,
                run_id=run_id,
                error_code=DRAWING_ANALYSIS_FAILED,
                expected_input_revision=input_revision,
            )
            return
        snapshot: dict[str, Any] = {"result": candidate}
        if result.topic_compatible is False:
            # ``candidate`` forbids extra keys, so the warning sits beside it (T2B-D7).
            snapshot["warnings"] = [{"code": "TOPIC_MISMATCH"}]
        repository.record_understanding(
            principal=principal,
            run_id=run_id,
            result_snapshot=snapshot,
            candidate_subject=subject,
            confidence=confidence,
            expected_input_revision=input_revision,
        )


__all__ = ["ParentInputJobRunner", "candidate_from_result"]
