# FEAT-018 Progressive Qwen multimodal understanding plan

Status: `IMPLEMENTED — owner Lightning smoke pending`

Feature: `FEAT-018-live-image-canvas-flow`

Branch: `codex/feat-018-contract-plan`

Date: 2026-09-22

Related implemented plan: `TOPIC_AND_T2_ACTIVITY_MATCHING_FIX_PLAN.md`

## 1. Owner decisions captured for this revision

The owner supplied these constraints for the next fix:

1. The default analysis should use one Qwen request. If the user chooses a different direction,
   the backend must issue a new query and re-check the image/narration instead of silently
   reusing the previous proposal.
2. The displayed topic should be one Vietnamese sentence of approximately 10–18 words.
3. The final understanding must combine image evidence and narration evidence. The result must
   preserve both sources, compare their confidence/support, and produce a grounded overall picture.

No implementation is authorized while this plan is `DRAFT` or `AWAITING_APPROVAL`.

## 2. Problem statement and current diagnosis

The latest owner screenshot shows the app entering Scene Understanding with `0 Thực thể`, no
claim cards, and a disabled Gate-A button. The current live path accepts a technically schema-valid
Vision V2 success even when all observation arrays are empty. `runAiSimulation()` then treats any
`SUCCEEDED` response as usable, stores an empty claim list, changes the session to
`GATE_A_PENDING`, and navigates to the Gate-A screen.

The existing V2 contract allows an all-empty technical success. That is valid for a low-level
adapter contract but is not a valid FEAT-018 Gate-A proposal: Gate A needs at least one grounded
claim or an explicit typed no-result/retry state. The current Lightning prompt also asks for strict
shape but does not make the useful-content requirement strong enough, and the bounded schema repair
currently runs for shape/schema failures rather than for an empty semantic result.

The prior topic/T2 fix improved ranking after claims exist; it cannot help when the provider returns
no claims. This plan therefore adds a bounded semantic-output guard, staged workflow projections,
image+narration fusion, and explicit user-directed re-query behavior.

## 3. Goals

- Prevent an all-empty Qwen result from appearing as a successful Gate-A proposal.
- Keep the strict `VisionUnderstandingResultV2` provider boundary and validate every provider result
  before it becomes an application claim.
- Make the normal path one Qwen generation, with at most one bounded repair generation when the
  first result is malformed, schema-invalid, or semantically empty.
- Publish sanitized understanding stages progressively so the UI can show useful progress without
  returning one oversized final JSON object at the first step.
- Preserve separate image, ASR, and typed-text provenance and combine them deterministically.
- Produce a grounded Vietnamese topic in the 10–18-word range when enough evidence exists.
- Re-query only when the adult/user explicitly chooses a different direction, and never run an
  unbounded or duplicate query for the same direction.
- Keep Gate A mandatory and block P1/T2 when the fused proposal has no grounded claim or unresolved
  hard conflict.
- Preserve the future auth/save seam, Android Emulator target, synthetic/non-child data boundary,
  Pixi continuity, no-video scope, and owner-only Lightning execution boundary.

## 4. Non-goals and preserved boundaries

- No video generation, video upload, or video player integration.
- No auth, durable save, child data, Firebase data products, mobile Lightning token, or provider
  endpoint.
- No FEAT-003 V2 schema mutation, Qwen adapter fork, or arbitrary LLM-generated activity.
- No automatic retry loop controlled by the client.
- No streaming of raw model tokens, raw JSON, prompts, image bytes, audio bytes, or provider text.
- No inference of age, readiness, supervision, materials, policy flags, or eligibility from image,
  ASR, or text.
- No silent replacement of an original image or its provenance.

## 5. Target end-to-end workflow

```text
image admission
      |
      v
explicit analysis request (image + optional ASR/TEXT)
      |
      +--> stage 1: narration evidence ready
      |
      +--> one Qwen image understanding request
                 |
                 +--> schema/semantic empty guard
                       |
                       +--> optional bounded repair once
      |
      v
stage 2: image claims ready
      |
      v
stage 3: fused proposal ready
  image claims + narration claims + confidence/support + conflicts
      |
      v
stage 4: topic ready
  10–18-word Vietnamese grounded topic + ranked directions
      |
      v
adult Gate A review/correction
      |
      +--> same direction: continue with stored proposal
      |
      +--> different direction: explicit re-query, new revision, re-fuse, re-score
      |
      v
P1/T2 -> ExperienceSpec -> Gate B -> Pixi source-art handoff
```

The model response itself remains a complete validated provider result. “Progressive” means the
backend exposes validated projections after each application stage; it does not parse or publish
partial invalid model JSON while Qwen is still generating.

## 6. Contract strategy

### 6.1 Keep existing contracts stable where possible

- Keep `VisionUnderstandingRequestV2` and `VisionUnderstandingResultV2` unchanged and FEAT-003-owned.
- Keep `RawUnderstandingResultV1` as the Gate-A raw handoff and preserve its image/ASR/fused/conflict
  fields and provenance rules.
- Keep `MobileWorkflowCommandV1` and `MobileWorkflowResultV1` as transport envelopes.
- Do not put raw provider output or a second parallel VLM schema in the mobile app.

### 6.2 Add a typed FEAT-018 progress projection only if needed

The current `WorkflowJobV1`/session infrastructure is the appropriate seam for staged progress. The
implementation should introduce a reviewed `UnderstandingProgressV1` projection, or a compatible
minor extension to the existing workflow payload, with these closed fields:

- `run_id`, `session_id`, `stage`, `stage_status`, `sequence`, `updated_at`;
- `source_status`: image, ASR, typed text, and their source hashes/opaque refs only;
- `image_claims`, `narration_claims`, `fused_claims` as sanitized typed projections;
- `topic`: text, word count, confidence/support state, primary claim ID, direction revision;
- `conflicts`, `reason_codes`, `repair_attempted`, `provider_attempt_count`;
- `gate_a_ready` and `terminal_failure` with closed codes only.

The exact contract name/version and whether the projection is a new `1.0` contract or a compatible
minor payload addition must be decided during approval. A breaking change to an existing frozen
contract is not allowed implicitly. The projection must remain backward-compatible with clients that
still wait for the current terminal `MobileWorkflowResultV1`.

### 6.3 Stage states

The proposed closed stage set is:

| Stage | Meaning | Gate-A allowed? |
|---|---|---:|
| `QUEUED` | Explicit request accepted; no provider result yet | No |
| `NARRATION_READY` | `NONE`, `TEXT_TYPED`, or successful ASR evidence stored | No |
| `IMAGE_CLAIMS_READY` | Validated Qwen image claims available | No |
| `FUSION_READY` | Image and narration claims reconciled with provenance/conflicts | No |
| `TOPIC_READY` | Ranked topic and direction candidates available | Yes, if claim guard passes |
| `REQUERY_RUNNING` | User explicitly selected a new direction | No |
| `BLOCKED_NO_GROUNDED_CLAIMS` | No usable claim after bounded repair/re-query | No |
| `FAILED` | Typed provider/input/runtime failure | No |

`TOPIC_READY` requires at least one grounded claim, a non-empty topic, source provenance, and no
unresolved identity/session conflict. An all-empty technical V2 success can be recorded internally
for diagnostics but cannot become a successful Gate-A proposal.

## 7. Qwen prompt and response hardening

### 7.1 Initial image prompt

Update the canonical Lightning prompt to require:

- one strict JSON object with the current five root arrays and no explanation;
- at least one concrete grounded entity when a recognizable object/mark is visible;
- a broad but visible fallback label only when the image is genuinely ambiguous;
- no all-empty response for a non-empty admitted image unless a closed `NO_GROUNDED_CLAIMS`
  outcome is explicitly selected by the adapter/application;
- an action only when visually anchored to an entity;
- a theme/context only when visible or supported by a separate narration stage;
- numeric confidence for every emitted entity/action/relation/theme;
- unique IDs and valid references;
- specific subjects before scenery/background;
- no psychological, developmental, eligibility, or activity claims.

The prompt must clarify that narration is context for disambiguation, not permission to invent a
visual entity. Image claims remain marked as image/vision evidence.

### 7.2 Empty semantic-result guard

After strict parse, bounded normalization, full schema validation, and policy validation:

1. Count grounded observations across entities, actions, relations, and themes.
2. If count is non-zero, publish `IMAGE_CLAIMS_READY`.
3. If count is zero on the first attempt, issue one targeted repair generation with a closed reason
   `EMPTY_GROUNDED_OUTPUT`, asking Qwen to re-inspect visible marks and emit only grounded claims.
4. If the second result is still empty, return a typed blocked/no-result stage. Do not enter
   `GATE_A_PENDING`, do not show a fake topic, and do not call P1/T2.

The repair shares the existing hard attempt budget. It must not trigger for provider timeout, device
failure, input-integrity failure, policy block, or user cancellation. The response must record only
attempt count, repair state, and closed diagnostic codes.

### 7.3 Direction re-query

When the adult selects a direction that differs from the current proposal, the client sends an
explicit command containing:

- the current session/version and idempotency key;
- the prior `run_id` and topic revision;
- selected direction/claim IDs and the adult-entered correction, if any;
- no image/audio bytes; the backend reuses the admitted artifacts.

The backend must:

- compare a deterministic direction signature with the previous run;
- replay the same request without a new provider call when the signature is unchanged;
- create a new run revision when it differs;
- query Qwen with the direction as a bounded adult hint, while still requiring visible evidence;
- re-run schema validation, empty guard, image+narration fusion, topic generation, and catalog
  matching;
- retain the previous proposal until the new run reaches a valid `TOPIC_READY` state;
- fail closed and keep the previous proposal if the new direction is unsupported.

The demo should cap direction re-queries per session at one unless a revised quota approval allows
more. The provider-generation budget must be explicit: initial run plus at most one repair, and one
user-directed re-query plus at most one repair. The owner must confirm this budget against the
existing approximately 25 Lightning credits before live smoke.

## 8. Image + narration fusion design

### 8.1 Normalize sources without overwriting them

Create a provider-neutral internal evidence row for each claim:

```text
claim_id
label / normalized concept
kind: subject | action | story | relation
source: VISION | ASR | TEXT_TYPED | FUSED_PROPOSAL
source_claim_ids
source_confidence: numeric or null when unavailable
evidence_refs
```

Image claims come from validated Qwen output. ASR claims come from the existing ASR contract and
segment confidence when supplied. Typed text is retained as `TEXT_TYPED` with no fabricated numeric
confidence. The original raw result remains immutable; fusion is a derived proposal.

### 8.2 Deterministic agreement and conflict policy

- Normalize reviewed aliases (`butterfly`/`con bướm`) into one concept key while preserving both
  source labels.
- When image and narration support the same concept, create one fused candidate with both source
  IDs and an agreement reason.
- When they provide compatible roles, use the image subject plus narration action/context.
- When they disagree, preserve both candidates, create a closed conflict record, and do not silently
  replace the image claim with narration. Gate A must show the disagreement and require adult choice.
- When only narration names a subject, allow a `NARRATION_SUPPORTED` topic proposal only if the UI
  clearly labels the source and Gate A remains mandatory. P1/T2 may use it only after the existing
  strict anchor/catalog checks succeed; otherwise return a typed no-eligible result.
- When only image evidence exists, proceed normally with `VISION` provenance.
- When both sources are absent/empty, block with `BLOCKED_NO_GROUNDED_CLAIMS`.

### 8.3 Confidence/support scoring

Do not pretend that model confidence is calibrated across VLM, ASR, and typed text. Preserve each
source confidence separately and compute a bounded derived `support_score` only for ranking:

- one numeric source: use that source confidence as the base;
- two agreeing numeric sources: use a documented weighted combination and an agreement reason;
- typed text: keep numeric confidence null and use a qualitative `TEXT_TYPED_SUPPORT` reason rather
  than inventing a number;
- conflict: apply a deterministic penalty and set `requires_adult_choice=true`;
- background/scenery: apply the existing background penalty;
- subject/action specificity and visible centrality remain ranking tie-breakers.

The exact weights must be written as a versioned policy constant and tested. The UI must call this a
support/ranking score, not a clinical or calibrated probability.

## 9. Topic composition

The backend, not the UI, owns the final topic text. It will use a deterministic bounded composer:

1. Choose the highest-ranked confirmed/fused subject that is supported by the image, narration, or
   both, while respecting conflict and provenance.
2. Add one compatible visible action when available.
3. Add one concrete context/theme when available.
4. Produce one Vietnamese sentence of 10–18 words where possible.
5. If the evidence cannot support 10 words, use a shorter truthful sentence and return a
   `TOPIC_SHORT_BECAUSE_EVIDENCE_LIMITED` reason instead of padding with invented details.
6. Never add an animal, object, action, location, emotion, or educational goal not present in the
   evidence.

Examples:

- `Con bướm màu cam đang bay gần bông hoa đỏ trong bức tranh` — only if those details are supported.
- `Con bướm đang bay gần bông hoa` — when color/background are not reliable.
- `Bức tranh có một con bướm được nhắc đến trong lời kể` — narration-only support.

The topic, word count, source badges, confidence/support reasons, and claim IDs must be returned in
the stage projection and stored with the Gate-A proposal.

## 10. Backend/API implementation plan

1. Extract the current synchronous understanding pipeline into explicit stage functions:
   narration preparation, Qwen call, validation/empty guard, fusion, topic composition, and final
   RawUnderstanding mapping.
2. Add a process-local progress/job record behind the existing session/application port. Do not put
   provider objects or raw payloads in the record.
3. Add a progress read endpoint or pollable result using the approved `WorkflowJobV1` seam. Keep
   idempotency/session-version checks on every command and read.
4. Add the explicit direction re-query command and bounded run revision state. Reuse the original
   image/audio artifact references and hashes.
5. Add an application-level empty-claim guard before `GATE_A_PENDING`. Map blocked/no-result to a
   stable safe code after contract review; do not overload a provider schema error without recording
   the reason.
6. Update `RawUnderstandingResultV1` mapping so image, ASR, typed-text, fused and conflict evidence
   remain traceable. Any new cross-boundary field requires a reviewed versioned contract.
7. Keep P1/T2 invocation behind `TOPIC_READY` and use the latest valid direction revision only.
8. Update logs to emit only stage, counts, confidence buckets, source statuses, run revision,
   attempt count, repair state, and closed reason codes.

## 11. Mobile/UI implementation plan

1. Replace the current “success means Gate A” behavior with stage-aware rendering.
2. Show `Đang nhận diện chủ thể`, `Đang đọc lời kể`, `Đang ghép thông tin`, and `Đang tạo chủ đề`
   based on sanitized progress.
3. Keep the source image, typed/ASR transcript, and claim cards visible while stages advance.
4. Disable Gate A until `TOPIC_READY` and at least one grounded claim exists.
5. Show a clear blocked state for empty output: `Chưa nhận diện được chủ thể rõ ràng`; provide an
   explicit retry button and do not show a fake topic/activity.
6. Show each claim's source (`Ảnh`, `Giọng kể`, `Nhập tay`, `Ảnh + lời kể`) and support/conflict
   reason. Do not display raw model JSON.
7. When the adult chooses a different direction or changes the correction, send the explicit
   re-query command. Show a new run revision and retain the previous proposal until replacement is
   valid.
8. On re-query failure, restore the last valid proposal and explain that the selected direction was
   not supported by the image/narration.
9. Keep the existing BaoVC React Native shell, Android Emulator target, future auth seam, and Pixi
   handoff unchanged after Gate A.

## 12. Verification plan

### Backend/unit

- Qwen valid rich output produces non-empty image claims.
- All-empty technical V2 success triggers one empty-output repair and then blocks if still empty.
- Repair cannot invent a claim, bypass source identity, duplicate IDs, broken references, or policy.
- Stage order is monotonic and terminal stages cannot regress.
- Image-only, ASR-only support, typed-text support, agreeing multimodal evidence, and conflicting
  evidence each preserve provenance.
- Confidence/support ranking is deterministic and uses no fabricated typed-text confidence.
- Topic length is 10–18 words when evidence permits; short fallback is explicitly reasoned.
- Same direction signature is idempotent; changed direction creates one new run revision and query.
- Re-query cannot bypass Gate A, session version, hard credit cap, or catalog eligibility.

### Contract/API

- Progress payload has no raw provider output, prompt, secret, absolute path, or media bytes.
- Existing terminal `MobileWorkflowResultV1` behavior remains compatible for old clients.
- All-empty result cannot transition session to `GATE_A_PENDING`.
- P1/T2 only receives the latest adult-confirmed fused anchor and exact provenance.
- Retry/idempotency/stale-version behavior is covered for initial run and direction re-query.

### Frontend

- Stage progress renders in the correct order.
- Empty result shows retry/block state, never `0` claims with an enabled/expected Gate A flow.
- Topic and source badges render from backend projection.
- Image/narration conflict requires adult choice.
- Changed direction triggers a re-query; repeated same direction does not duplicate it.
- Latest valid proposal reaches Gate A, P1/T2, ExperienceSpec, Gate B and Pixi without identity drift.

### Owner Lightning smoke

The owner manually runs synthetic/non-child tests only; Codex does not call Lightning. The smoke
matrix should cover:

1. image-only drawing with a clear subject;
2. image plus ASR agreeing with the subject/action;
3. image plus narration conflict;
4. typed narration when audio is unavailable;
5. first empty/weak response followed by bounded repair;
6. adult selecting a different direction and observing exactly one new query;
7. repeated retry/idempotency and no runaway credit consumption.

Record only sanitized stage outcomes, counts, attempt numbers, latency, reason codes, and hashes in
feature-local evidence. Stay within the existing approximately 25-credit ceiling; the revised
per-session provider budget must be approved before live execution.

## 13. Acceptance criteria

1. A normal explicit analysis produces at least one grounded claim or a typed blocked/no-result
   state; it never enters Gate A with an empty claim list.
2. The default run uses one Qwen request, with no more than one bounded repair when required.
3. The UI receives sanitized progressive stages and does not need to wait for one oversized final
   JSON before showing narration/image progress.
4. Image and narration claims remain separately attributable and are fused using deterministic,
   tested support/conflict rules.
5. A user-selected new direction triggers a new backend query; the same direction is idempotent.
6. The final topic is Vietnamese, grounded, and normally 10–18 words, with a reason when evidence
   is too limited for that length.
7. Conflicts are visible to the adult and cannot silently select a contradictory anchor.
8. No raw provider content, credentials, media bytes, child data, or absolute paths enter logs,
   progress payloads, mobile code, commits, or evidence.
9. Existing Gate A/P1/T2/Gate B/Pixi identity and future auth/save boundaries remain intact.
10. Focused tests, TypeScript, architecture/security validators, diff checks, and owner-smoke
    evidence pass before the plan is marked complete.

## 14. Implementation record — 2026-09-22

- Approval was recorded in `approvals/TASK_APPROVAL.md` with the plan SHA-256
  `2FE85477B41BA7C64C98E200DBF284E28D7783123EC3CD26721C3AEF58B2B384` before code changes.
- The compatible progress transport is the existing `MobileWorkflowResultV1` payload with a typed
  `understanding_progress` object plus `GET /v1/sessions/{session_id}/understanding/progress`.
  It contains only sanitized stage metadata and typed claim IDs/counts; the provider response stays
  complete and synchronous, while the projection is available for polling and stage-history UI.
- `BLOCKED_NO_GROUNDED_CLAIMS` is the closed stage value; `NO_GROUNDED_CLAIMS` is the closed
  application reason code. It never transitions the session to `GATE_A_PENDING` on the initial run.
- Fusion uses reviewed alias agreement only. The numeric support value for a fused claim is the
  validated vision confidence; typed text remains qualitative and never gets fabricated confidence.
  Conflicts are preserved as `SOURCE_DISAGREEMENT` and remain adult-reviewable.
- Provider budget is one normal generation, at most one internal schema/semantic repair, and at
  most one explicit changed-direction re-query with its own single repair opportunity. Codex does
  not trigger Lightning; the owner performs smoke tests within the approved approximately 25-credit
  ceiling.
- Changed files include the Lightning Qwen adapter/prompt, live image demo orchestration and
  progress endpoint, raw multimodal mapper, BaoVC client/context, and focused contract/unit tests.
  No video, auth, durable save, mobile credentials, child data or FEAT-003 schema change was added.

## 15. Verification result

- `pytest -q backend/tests` passed with six existing skips when the repository root and
  `backend/src` were supplied on `PYTHONPATH`.
- Focused Qwen/FEAT-018 tests cover semantic-empty repair, empty-result Gate-A blocking, image plus
  typed-text fusion, bounded topic length, changed-direction re-query and progress polling.
- Ruff, mypy on changed backend modules, `pnpm` mobile TypeScript, `compileall`, `git diff --check`
  and `python tools/validate_repository_security.py` passed. Owner Lightning/Android smoke is the
  only remaining execution step and remains outside Codex's authority.
