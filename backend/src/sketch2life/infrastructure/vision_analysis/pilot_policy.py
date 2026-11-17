"""Named retry bound for the guarded single-attempt vision pilot."""

from sketch2life.domain.ai_jobs.model import JobRetryPolicy

PILOT_VISION_RETRY_POLICY = JobRetryPolicy(
    "pilot.vision_single_attempt.v1",
    max_attempts=1,
    backoff_base_ms=0,
    backoff_multiplier=1,
    backoff_max_ms=0,
    attempt_timeout_ms=180_000,
)

__all__ = ["PILOT_VISION_RETRY_POLICY"]
