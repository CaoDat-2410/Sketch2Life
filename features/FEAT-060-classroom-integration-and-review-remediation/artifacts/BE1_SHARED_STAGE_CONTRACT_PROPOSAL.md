# BE1 additive contract proposal: shared classroom learning stage

**Status: IMPLEMENTED LOCALLY under FEAT-060 Plan Rev4; not yet BE1-owner reviewed or PostgreSQL-verified.** This proposal is retained as design history. The implementation is in `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`, contracts in `backend/src/sketch2life/contracts/schemas/be1_runtime.py`, and migration `backend/alembic/versions/20261024_0005_classroom_srs_contracts.py`. See the current API catalogue for exact endpoints, guards, and limits. No external BE1 review is claimed.

## Nói ngắn gọn

SRS chia một buổi học thành 9 chặng. BE1 hiện biết **buổi học đang ở trạng thái vận hành nào** (`configured`, `lobby`, `active`, `paused`, `finished`) nhưng chưa lưu **lớp đang ở chặng học nào** (ví dụ `explore_draw` hay `reflection`). Đề xuất là thêm trạng thái chặng học có lưu trên backend để khi tải lại trang, mọi người vẫn thấy đúng chặng; thao tác “Tiếp tục” phải được BE xác nhận, không chỉ đổi màn hình.

Owner đã xác nhận phải lưu phân biệt hai trường hợp: **hoàn tất đủ quy trình** hoặc **giáo viên kết thúc sớm**. FEAT-060 Rev4 bổ sung route/field/receipt và migration cục bộ; chưa chạy migration lên database và chưa được BE1 owner review.

## Why this contract is needed

The Master SRS B5 defines nine ordered shared learning stages; B19.4 defines their lower-snake-case values and says stage is independent from session lifecycle. Current BE1 persists `configured`, `lobby`, `active`, `paused`, `finished`, but has no shared-stage row or transition endpoint. Existing `finish` cannot be used to claim `Completed` or `EndedEarly`. Membership progress is per child, not per stage. Frontend-only stage state would be lost/reorderable and would let clients claim SRS gates that the backend has not checked.

## Proposed stable values and separation

```text
preparation → join → explore_draw → assistance → sharing → knowledge → off_screen → reflection → completion
```

- Keep lifecycle (`configured/lobby/active/paused/finished`) separate from shared stage.
- Keep each group's activity progress separate from the shared class stage.
- **Owner-confirmed policy:** Teacher may advance only to the next stage after backend guards and a durable receipt; arbitrary skips are rejected. Assistance may be requested/reviewed while the shared stage remains unchanged, or Teacher may explicitly record `not_needed` when no assistance is needed. The `assistance` stage remains an explicit shared stage when selected by Teacher.
- Do not add `completed` or `ended_early` to the lifecycle enum as an undocumented remap. Completion is an outcome command with an explicit reason/outcome and persistence receipt.
- **Owner-confirmed interim policy:** return to prior stages remains blocked until SRS `OD07` is resolved. OD07's final pedagogical rule remains open. Never implement a UI Back button as a domain rewind.

## Proposed endpoints (versioned inside BE1 v1)

### Read authoritative state

`GET /api/be1/v1/organizations/{org}/sessions/{session}/learning-stage`

Adult: assigned teacher/school admin. Returns:

```json
{
  "contract": "Be1SharedLearningStageV1",
  "session_id": "...",
  "stage": "explore_draw",
  "stage_revision": 4,
  "lifecycle_state": "active",
  "entered_at": "...",
  "last_command_id": "..."
}
```

No child names, artwork, AI output, or provider details are included in this controller response.

### Advance shared stage

`POST /api/be1/v1/organizations/{org}/sessions/{session}/learning-stage/advance`

Header: `Idempotency-Key` (required). Body:

For the sample below, the class is already at shared stage `assistance`, revision 5. If no assistance is needed, Teacher records that disposition while advancing to the next stage `sharing`.

```json
{
  "expected_stage_revision": 5,
  "target_stage": "sharing",
  "assistance_disposition": "not_needed",
  "unfinished_group_disposition": "save_draft"
}
```

**Owner-confirmed policy:** if any group has unfinished work when the class advances, Teacher must select `save_draft`; this choice is required for that command, and the durable draft must remain attached to the group. It does not mark that group complete or prevent other groups from progressing. `assistance_disposition=not_needed` is a proposed representation of the owner's explicit no-assistance choice; BE1 must confirm its wire shape. The command returns the persisted stage, incremented `stage_revision`, event/command ID, disposition and guard outcomes. Repeating the same idempotency key and body returns the original receipt; reuse with a different body is a conflict.

Server guards proposed:

- Teacher assignment + organization/class/session scope verified.
- Session lifecycle must be `active` for normal advance; the stage is not advanced by UI navigation, group-ready status, background AI completion, or child calls.
- `expected_stage_revision` must match; stale command returns 409 plus current revision/state (no implicit retry).
- Target must be the next SRS stage. Arbitrary skip transitions are rejected. Return transitions are disabled until OD07 is resolved and a later decision approves a specific transition.
- Stage-specific mandatory durable outcomes are checked before advance; the exact gate table below is proposed for review.
- Consent is rechecked for any data/media artifacts entering a stage; a failed guard blocks without moving the stage.
- The stage transition and append-only event are committed atomically.

### Explicit completion outcome

`POST /api/be1/v1/organizations/{org}/sessions/{session}/completion`

Header: `Idempotency-Key` (required). Body proposal:

```json
{
  "expected_stage_revision": 8,
  "outcome": "ended_early",
  "reason_category": "time",
  "teacher_note": null,
  "unfinished_group_disposition": "save_draft",
  "outcome_refs": ["artifact:...", "observation:..."]
}
```

Potential `outcome` values: `completed` and `ended_early`. **Owner-confirmed:** `ended_early` requires category `time`, `safety`, `technical`, or `other`; a short Teacher note is optional. The existing lifecycle may remain `active/paused → finished` for compatibility, while the completion receipt records product outcome separately. Before implementation, BE1 owner must choose whether the result belongs in a dedicated session-outcome table, event stream, or another approved persisted model. No stage/source data is erased by early end; unfinished group art must be dispositioned explicitly using the owner-approved `save_draft` policy.

## Proposed stage guard matrix (requires BE1/product validation)

| Target stage | Proposed minimum durable precondition before leaving it |
|---|---|
| `preparation` → `join` | Session config validates required class, topic, age, tools, preset version, grouping and purpose. Opening the lobby is an explicit persisted command. Current generic JSON config does not validate these requirements. |
| `join` → `explore_draw` | At least one admitted child; every admitted child has current effective consent; each active device mapped to a managed profile; Teacher presses Start. Current BE1 checks admitted+consent but assignment mapping is not queryable. The owner-confirmed SRS classifies 40 concurrent children as an unmeasured pilot capacity target, not a hard count rejection. |
| `explore_draw` → `assistance` | Active canvas/group state is checkpointed; unfinished groups receive the required `save_draft` disposition; accepted operations have durable revisions; current turns are closed or preserved according to a teacher-selected disposition. Checkpoint production storage is TBD. |
| `assistance` → `sharing` | Assistance has a durable outcome or explicit `not_needed`; no AI result is surfaced without its exact source, safety/policy decision and Teacher approval. FEAT-057 gates apply. |
| `assistance` → `sharing` | Each AI result shown to a child has exact source version, safety/policy decision, Teacher approval, and availability/decline outcome; failure/stale results remain unavailable. FEAT-057 gates apply. |
| `sharing` → `knowledge` | Teacher explicitly selects and publishes session artifact/gallery audience; contributor consent rechecked; child presentation/decline outcome captured if required by the final SRS test. Gallery routes exist; FE integration and production artifact storage are pending. |
| `knowledge` → `off_screen` | Selected media reaches a terminal ready/reviewed state; exact version has Teacher approval and playback/skip receipt. No autoplay of unapproved media. FEAT-057 gates apply. |
| `off_screen` → `reflection` | Activity assignment, preparation/material/safety checks, and an explicit performed/skipped/failure outcome are saved. Candidate activity API is not mounted. |
| `reflection` → `completion` | Child reflection outcome (including explicit no-response), Teacher observation and confirmed assessment if applicable are saved; no AI-only assessment. Current BE1 only supports adult-authored observations. |
| `completion` → terminal outcome | Final artifact/progress/observation/outcome refs are durable; no pending required writes/reviews; completion snapshot and selected unfinished-group disposition are persisted atomically. Current APIs do not provide this transaction. |

This matrix is a proposal, not an approved interpretation of every SRS rule. The B19.5 and B19.6 guards and outstanding product decisions must be reviewed by the BE1 owner before coding.

## Data model proposal

Proposed additive table (name illustrative, schema review required):

```text
classroom_session_stage
- organization_id, session_id (scope/FK)
- stage (enum/check using exact 9 values)
- stage_revision (monotonic per session)
- entered_at, updated_at
- last_command_id (idempotency receipt)
```

Append transition events to the existing session event/audit mechanism with `from_stage`, `to_stage`, actor, command ID, revision, disposition, and guard result codes. Completion outcome and snapshot references need an owner-approved persistence design. No migration is drafted here because the repository has multiple migration heads/roots and BE1-owned upgrade order is unresolved (SR-03).

## Required decisions / review checklist

1. **Project-owner policy resolved:** stage progression is next-only, Assistance may interleave or be recorded `not_needed`, and arbitrary skips are forbidden. BE1 must review exact wire representation and guards.
2. Approve stage revision as separate from session lifecycle revision; confirm same idempotency-key rules.
3. **Project-owner policy resolved:** unfinished group work requires `save_draft` before the class advances. BE1 must review its durable receipt/recovery/transaction contract.
4. **Project-owner policy resolved:** no rewind until OD07 is resolved; OD07 itself remains OPEN. Arbitrary skips are forbidden.
5. Confirm the guard matrix against B19.5/B19.6 and final acceptance scenarios.
6. Choose persistence home for stage history/completion outcomes and approved migration root/order.
7. **Project-owner policy resolved:** `completed` differs from `ended_early`; the latter requires a reason category (`time`, `safety`, `technical`, `other`) and permits an optional note. BE1 must review exact receipt/fields/guards while retaining compatibility `finished` semantics.
8. **Resolved by SRS v3.2 B17/OD12:** 40 concurrent children is an unmeasured pilot capacity target, not a hard admission cap. A new owner decision would be required before BE1 rejects admissions at that count; capacity still needs a measured load profile.

## Review/implementation gate

No schema, migration, route, frontend stage controls, persisted enum, or lifecycle transition should be implemented from this proposal until BE1 owner (Khoa) and project owner review the exact contract and the feature approval record is updated with the approved revision/hash. The user selected the proposal route; this document is the review artifact requested.
