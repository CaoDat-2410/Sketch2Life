# StoryRun-lite Modal diagnosis and cleanup port contract — 2026-11-03

Status: **APPROVED / IN PROGRESS**, based on the owner's direct instruction in this thread. This supplements previous live plans and their historical records.

The SQL repository reports quarantine cleanup success as `True` and recoverable filesystem failure as `False`; startup recovery counts those outcomes. Other callers may ignore the result. Correct the `StoryRunLiteRepositoryPort.remove_upload_quarantine` return annotation from `None` to `bool`, documenting that contract; no runtime behavior, migration or unrelated port changes. Recheck all implementations, callers and relevant recovery behavior, and run focused tests, mypy and applicable harness checks. Authorized source file: `backend/src/sketch2life/application/ports/story_run_lite.py`; tests may only be changed if genuinely needed to verify this contract, with evidence recorded.

Inspect prior Modal app status and available startup, image, Volume, Secret, queue and GPU information without exposing credentials. Distinguish confirmed observations from hypotheses. If the blocker can be resolved, run a new temporary `modal serve` from a clean committed archive, use an appropriate bounded `/health` timeout, and proceed with at most one guarded inference request only after health, isolated task DB, real scanner and worker gates pass. After `SENT`, an ambiguous outcome is UNKNOWN and is never retried. Stop temporary app/processes and preserve task DBs. No persistent deployment, stage, commit, push or merge.

Record actual outcomes, missing information, process cleanup, evidence/status and an additive snapshot. Never put bearer, DB password, DB URL or sensitive image/model response in logs.
