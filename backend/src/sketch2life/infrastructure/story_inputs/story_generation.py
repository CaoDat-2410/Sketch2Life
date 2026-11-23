"""Run the story generation of a rewrite after the 202 response (goal v3 T-2d, SRS l.394, l.1668).

``POST /v1/story-runs/{id}/story-rewrites`` reserves the revision and answers 202; the generation is
the work of ``ParentStoryRewriteRunner.run``, scheduled through ``BackgroundTasks`` when a story
generator is composed (``app.state.story_generator``, OD-13 owns the real worker). With none
composed the run waits in ``SCRIPT_GENERATING`` with ``job_state QUEUED`` and the adult can cancel
it. FastAPI closes the request's dependencies before background tasks run, so the runner opens its
own session and closes it.

Outcomes, each written under the run lock (a run cancelled while the generator worked, or a
revision no longer ``GENERATING``, is discarded and changes nothing):

* a draft that passes ``story_output`` is stored: the run moves to ``SCRIPT_REVIEW``;
* a draft that fails validation, or ``StoryGenerationFailure``: ``fail_story_revision`` records a
  stable code. A rewrite goes back to the previous reviewable story (``SCRIPT_REVIEW``, job
  ``FAILED``, ``retryable`` while the slot has attempts left; T-2d-fix D1), a first story ends the
  run ``FAILED``;
* ``StoryGenerationOutcomeUnknown`` or any unexpected error: ``SCRIPT_GENERATION_UNKNOWN``
  (reconciliation, never an automatic retry; the story task reaper releases it at the 6 h AI job
  deadline).

Every failure write is a compare-and-set on the run state and the reserved revision: a late worker
after the reaper or after a new attempt changes nothing (409, discarded).

The worker input holds the child's profile context and the adult's idea, so it is never logged. The
adult's rewrite hint is untrusted data in its own field; the instruction is the constant below
(FR-AI-12 l.578, BR-36 l.280). The versioned child-safety screen of the hint does not exist yet
(recorded debt, one call site: ``RewriteStoryRequestV1``).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Final

from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    STORY_GENERATION_UNAVAILABLE,
    StoryGenerationFailure,
    StoryGenerationOutcomeUnknown,
    StoryGeneratorPort,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_actor import RunActor
from sketch2life.application.services.story_output import (
    StoryOutputInvalid,
    complete_generated_story,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    job_side_repository,
)

_LOGGER = logging.getLogger("sketch2life.api")

# The instruction of every rewrite (T2D-D6): a server constant, versioned, part of the receipt
# fingerprint. The wording is the default the owner may change (Q-2d-3); tests pin it.
REWRITE_NEUTRAL_INSTRUCTION_VERSION: Final = "rewrite-neutral.v1"
REWRITE_NEUTRAL_INSTRUCTION_V1: Final = (
    "Hãy viết lại câu chuyện theo một cách khác, giữ nguyên chủ thể và ý tưởng của người lớn."
)
STORY_REWRITE_PROMPT_VERSION: Final = "parent-story-rewrite.v1"
# Written on the reserved revision row until the generator reports its own identity.
STORY_REWRITE_MODEL_ID: Final = "story-generator-port"
STORY_REWRITE_MODEL_REVISION: Final = "unassigned"
STORY_OUTCOME_UNKNOWN: Final = "STORY_OUTCOME_UNKNOWN"

# Generator-supplied strings land in bounded columns (story.runs.error_code 64, provider_call_id
# 128, model_id 256, model_revision 128). An over-long value would fail the store write, which the
# runner swallows, and leave the run stuck in SCRIPT_GENERATING/RUNNING; so they are bounded first.
_ERROR_CODE_PATTERN: Final = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_CALL_ID_MAX: Final = 128
_MODEL_ID_MAX: Final = 256
_MODEL_REVISION_MAX: Final = 128


def bounded_error_code(code: object) -> str:
    """The generator's failure code when it is a stable upper-case code, else the generic one."""
    if isinstance(code, str) and _ERROR_CODE_PATTERN.fullmatch(code):
        return code
    return STORY_GENERATION_UNAVAILABLE


def _bounded(value: object, limit: int, fallback: str) -> str:
    text = value if isinstance(value, str) else ""
    text = text[:limit]
    return text if text.strip() else fallback


class ParentStoryRewriteRunner:
    def __init__(
        self, session_factory: Callable[[], Session], generator: StoryGeneratorPort
    ) -> None:
        self._session_factory = session_factory
        self._generator = generator

    def run(
        self,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        actor: RunActor | None = None,
    ) -> None:
        """Never raises: a background task has no caller to report to; failures are recorded.

        For a Teacher run ``actor`` selects the job-side repository bound to the organization the
        route put on the reservation (T-4b3a D6); a Parent run passes no actor."""
        session = self._session_factory()
        try:
            self._run(session, principal, reservation, actor)
        except ParentStoryRunError as exc:
            # Cancelled or purged work is discarded; a store outage leaves the run QUEUED/RUNNING.
            _LOGGER.info("parent_story_rewrite_discarded code=%s", exc.code)
        except Exception as exc:  # noqa: BLE001 - nothing may escape a background task
            _LOGGER.warning("parent_story_rewrite_error type=%s", type(exc).__name__)
        finally:
            session.close()

    def _run(
        self,
        session: Session,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        actor: RunActor | None,
    ) -> None:
        repository = (
            SqlParentStoryRunRepository(session)
            if actor is None
            else job_side_repository(session, actor, reservation.organization_id)
        )
        if not repository.start_story_generation(
            principal=principal,
            run_id=reservation.run_id,
            story_revision_id=reservation.story_revision_id,
        ):
            return
        try:
            result = self._generator.generate(reservation.worker_input)
        except StoryGenerationFailure as failure:
            self._fail(
                repository,
                principal,
                reservation,
                bounded_error_code(failure.code),
                unknown=False,
            )
            return
        except StoryGenerationOutcomeUnknown:
            self._fail(repository, principal, reservation, STORY_OUTCOME_UNKNOWN, unknown=True)
            return
        except Exception:  # noqa: BLE001 - a generator defect is an unknown outcome
            self._fail(repository, principal, reservation, STORY_OUTCOME_UNKNOWN, unknown=True)
            return
        try:
            complete_generated_story(
                repository,
                principal=principal,
                reservation=reservation,
                raw_story=result.story,
                provider_call_id=_bounded(result.call_id, _CALL_ID_MAX, "unassigned"),
                model_id=_bounded(result.model_id, _MODEL_ID_MAX, STORY_REWRITE_MODEL_ID),
                model_revision=_bounded(
                    result.model_revision, _MODEL_REVISION_MAX, STORY_REWRITE_MODEL_REVISION
                ),
            )
        except StoryOutputInvalid as invalid:
            # The failure is already recorded by the service.
            _LOGGER.info("parent_story_rewrite_invalid code=%s", invalid.code)

    @staticmethod
    def _fail(
        repository: SqlParentStoryRunRepository,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        code: str,
        *,
        unknown: bool,
    ) -> None:
        repository.fail_story_revision(
            principal=principal,
            reservation=reservation,
            error_code=code,
            outcome_unknown=unknown,
        )


__all__ = [
    "REWRITE_NEUTRAL_INSTRUCTION_V1",
    "REWRITE_NEUTRAL_INSTRUCTION_VERSION",
    "STORY_REWRITE_MODEL_ID",
    "STORY_REWRITE_MODEL_REVISION",
    "STORY_REWRITE_PROMPT_VERSION",
    "ParentStoryRewriteRunner",
]
