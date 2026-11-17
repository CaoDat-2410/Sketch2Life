# FEAT-063: Retest timed-out non-video AI with a 30-minute wait

**Status:** APPROVED / READY TO RUN  
**Date:** 2026-11-04 (Asia/Saigon)  
**Canonical product source:** FEAT-063 System Architecture SRS v2.3-draft; no SRS edit is included.  
**Approver:** Project owner, direct instruction: “thử tăng timeout lên tầm 30' rồi test lại xem”.

## Goal

Repeat the non-video GPU workloads that previously ended at a 600-second Modal capacity wait, raising only the client-side result wait to 1,800 seconds. Record whether capacity becomes available and whether the outputs satisfy the existing contracts.

## Approved scope

- Retest `drawing.analyze` with the same synthetic butterfly artwork, using the exact versioned drawing-worker manifest and new job/generation/attempt IDs.
- Retest `story.generate` / `storyboard.generate` once using the versioned worker client and a synthetic adult-confirmed Parent fixture. The already-tested StoryRun API and its adult-confirmation gate are not re-exercised in this capacity-only retest.
- Retest `parent.sketch-guide.generate`, `teacher.sketch-deck.generate`, `lesson.visual.generate`, and `drawing.segment` once each using generic or synthetic approved inputs.
- The maximum wait for each Modal function result is 1,800 seconds. Parent HTTP read timeouts must exceed that bound. Keep each worker's existing execution timeout unchanged; the observed blocker was queue/capacity wait.
- Use new job/generation/attempt IDs and a new task-owned evidence folder. Do not retry any existing unknown call or reuse the old StoryRun.
- Record per-call ID, start/end time, total wait, terminal state, output schema/integrity checks, and final Modal app/task state.

## Exclusions and safeguards

- No video scene generation, video composition, video validation, or final-safety inference.
- Do not repeat TTS/ASR, which succeeded in the prior retest. Keep `lesson.plan.suggest` undispatched while role/model selection remains unresolved.
- Synthetic artwork, synthetic approved lesson fixture, and generic topic/difficulty only. No real child/profile/voice/lesson data.
- Keep every product workload disabled. Do not change production defaults, quota policy, canonical SRS, or model selection.
- Do not retry an unknown result within this run. On the 1,800-second bound, cancel the outstanding call, record `UNKNOWN`, and continue with independent workloads.
- Stop every Modal `dev` app after the run and verify zero tasks. Retain shared Modal Volumes and unrelated Docker services.
- No commit, push, merge, or publication is included in this task.

## Acceptance criteria

1. Each previously capacity-blocked non-video workload receives at most one fresh dispatch with an 1,800-second client wait bound.
2. Drawing and story calls use the current versioned worker contracts; the story fixture records the already-confirmed synthetic subject and contains no profile or real-child data.
3. A successful model response is validated against its workload contract and remains a private draft/POC; HTTP `202` alone is not counted as inference success.
4. Every timeout, worker exception, and skipped dependent stage is reported with its actual state; no result is invented or silently retried.
5. No video inference occurs; all product workloads remain disabled; all Modal `dev` apps are stopped with zero running tasks after evidence collection.

## Planned evidence

- Runner and per-workload traces under `evidence/scripts/` and `evidence/assets/ai_nonvideo_30min_queue_retest_20261104/`.
- Summary report at `evidence/AI_NONVIDEO_30MIN_QUEUE_RETEST_RESULTS_20261104.md`.
- Additive updates to FEAT-063 status, evidence index, decision/context, and source registers.
