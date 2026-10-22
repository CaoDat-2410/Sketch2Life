# FEAT-057 cross-lane UoW owner decision D2 — 2026-10-21

- Decision source: direct owner response in the active conversation: “Chốt theo đề xuất cả 2”.
- Status: DESIGN DECISION RECORDED / NOT IMPLEMENTATION APPROVAL.
- Related review: Claude independent rereview 2, verdict CHANGES_REQUIRED.
- Related design: BE2-01 UoW scope Rev4 and FEAT-057 slice plan Rev5, both superseded for review by successors only.

## Decisions

1. A foundation completion with JobState SUCCEEDED and ResultDisposition.STALE must have an explicit terminal representation in the BE2-08 VideoRun contract. The selected direction is a distinct stale terminal state on the video-run lifecycle axis, added only through a versioned BE2-08 contract revision. It carries no accepted/playable artifact and does not change the foundation JobState enum. The current VideoRun model, codec, and worker receipt rules do not implement this state; no source or schema change is authorized by this decision.
2. BE2-08 binds attempt_id to a VideoRun only at boundary S. When a retry returns the run to QUEUED, it clears the previous run attempt_id. Attempt number remains foundation-owned and is not added to VideoRun. A queued run therefore has no active attempt_id, including after retry and before the next S commit.

## Scope and gates

These decisions settle the two owner choices raised from Claude finding F-01 stale mapping and F-03 attempt identity. They do not adopt the cross-card contract, approve code, schema, migrations, tests, or supplemental S/F implementation. The BE2-08 scope and codec must be revised and independently reviewed before any source change. BE2-01, BE2-08, and FEAT-057 supplemental approval remains pending.

Keep X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED. Budget unit and limit remain unprovided. Modal, Lightning, provider, server, database, and runtime remain outside this decision.

