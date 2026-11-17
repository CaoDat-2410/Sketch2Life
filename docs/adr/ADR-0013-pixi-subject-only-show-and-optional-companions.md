# ADR-0013: Subject-only Pixi shows with optional reviewed companions

- Status: ACCEPTED
- Date: 2026-10-03
- Owner: Sketch2Life project owner (plan revision 1 approval)
- Context: FEAT-035 C-01; FEAT-028 topic-asset eligibility; FEAT-030 Pixi AI show contracts.

## Context

The committed FEAT-028 catalog contains 144 records but none currently satisfies the strict runtime filter (`runtime_eligible`, reviewed `APPROVED`/`APPLIED`, and license `CLEARED`). The planner currently requires at least one candidate, selected asset, and asset read, so a required planner can prevent a valid source-subject show from starting. The current static asset gate protects visual review and rights and must not be bypassed to make the feature appear operational.

## Decision

- A Pixi show may be valid with zero supplemental asset IDs when every beat targets the confirmed source subject and its selected motion is supported by the verified source rig.
- Supplemental beats require exact approved candidate IDs. Every selected asset must be referenced, every referenced asset must be selected, and capability reads must exactly match the selected IDs. Existing human review, license, runtime eligibility, provenance, and hash checks remain mandatory.
- Subject-only and supplemental show semantics are introduced additively with a new contract version. Existing V1 contracts remain unchanged and continue to require their existing asset constraints.
- Missing/invalid essential rig, unsupported behavior, stale source, or invalid planner output remains a typed visible failure. The client does not silently downgrade to PIXI_V2 and does not claim show success.
- Planner calls remain explicit single attempts behind the configured backend adapter. No provider key/URL is sent to mobile; no live inference is authorized by this ADR.

## Consequences

- Backend and renderer validators must enforce the same empty-asset rule and beat/asset-reference invariants.
- Planner request schema may convey an empty candidate list only in the new contract version. Provider output is still untrusted and fully validated.
- Tests must cover empty-catalog subject-only success, rejected unapproved/referenced assets, invalid empty selections with supplemental beats, and unchanged V1 behavior.
- The empty-catalog case no longer blocks source-only movement but still cannot add any unreviewed companion sprite.

## Evidence

- Feature evidence: `features/FEAT-035-branch-review-remediation/evidence/notes/priority-verification.md`.
- Approved implementation plan: `features/FEAT-035-branch-review-remediation/plan/PLAN.md` (revision 1).
