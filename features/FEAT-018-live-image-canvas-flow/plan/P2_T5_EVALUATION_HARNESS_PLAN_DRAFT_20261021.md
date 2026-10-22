# FEAT-018 P2-T5 Evaluation Harness Plan

- Revision: 1.1
- Status: `APPROVED — BOUNDED OFFLINE SLICE ONLY; FULL TASK 5 OPEN; LIVE NOT AUTHORIZED`
- Date: 2026-10-22
- Planning branch: `feature/feat018-p2t5-evaluation-harness`
- Planning baseline: `b11bc7b870f615e493afb1bc723b888befdb58c9`, from
  `feature/feat018-p2t4-mapping-diagnostics`
- Branch and baseline were revalidated read-only under Person 2's scoped authorization; see the
  current approval below for the tracked/untracked inventory and warning.
- Workstream identity: `FEAT-018 P2-T5` / `FEAT018-P2-T5`. This is distinct from the existing
  `FEAT-003 P2-T5` fusion/evaluation implementation and tests in the repository. Do not reuse or
  collide with generic `p2_t5_*` modules; any reuse requires C0 review and explicit approval.

## Current approval - bounded offline slice

- Authority: Person 2 issuance `FEAT018_P2T5_BOUNDED_OFFLINE_APPROVAL_01`, recorded in
  `approvals/TASK_APPROVAL.md` at 2026-10-22 09:37:04 UTC.
- Approved source: revision 0.9, SHA-256
  `6E9550A045D9FC382F83FEACC0ACAF9B55A4423A5DE99C30E437C48071A1951E`.
- This revision synchronizes that actual issuance before implementation. Claude's owner-relayed
  `PASS WITH NOTES`/no-plan-blocker review applies to source rev 0.9 only; it is not a review of
  these successor bytes, implementation evidence, live authority, or a gate PASS.
- Revision 1.0 recorded the bounded offline approval. Revision 1.1 records the later remaining-gates
  disposition below; it does not change the approved offline scope.
- Person 2 confirms authority over APP hold and grants the current coordinator exactly one append
  for this issuance. The append has been read back; the original 53,232-byte prefix is unchanged
  (SHA-256 `D756F32A8EFFC047196D96BED2B7660CE04D7DFC8BC14A64637495F2BD865FF4`).
  APP hold remains IN FORCE outside that append; no further approval write is authorized.
- Branch and HEAD were verified read-only before the append:
  `feature/feat018-p2t5-evaluation-harness`,
  `b11bc7b870f615e493afb1bc723b888befdb58c9`.
  There were no tracked staged/unstaged changes and the source plan was untracked. Git warned
  that its global ignore file was inaccessible. These facts do not claim a clean worktree.
- Task status for the bounded offline slice: `APPROVED`. Full Task 5: `OPEN`.
  Full C0/A1/A2/A4/A5/A7/A8/A9 acceptance is not inferred from the slice approval.

### Approved D1-D4 and evidence boundaries

D1 permits independent unaffected offline implementation. OSError/transient attempt-number proof
remains HELD; no adapter fix or fabricated attempt count.
D2 permits fake characterization of the existing ASR/Vision rate-limit/provider-error asymmetry.
Task-level rate-limit/provider-error acceptance remains HELD/UNMAPPED, even if characterization
tests pass. No harness retry, live provider request, or mapping harmonization is authorized.
D3 retains all 120 primary slots (20 version-2 pilots x six families) with separate execution and
requirement status. HELD/UNMAPPED rows and required skips do not count as satisfied coverage.
D4 keeps unchanged quality-validator reference evidence separate from FEAT-018 HTTP-admission
provider-counter evidence. Neither proves the other boundary.

The C0 matrix uses `feat018-p2-t5-act-####-<family>` IDs, with families `exact`, `ambiguous`,
`no-match`, `conflict`, `low`, `adult-correction`. Pilot IDs are ACT-0004, 0016, 0019, 0020,
0023, 0026, 0030, 0033, 0039, 0046, 0055, 0058, 0061, 0067, 0074, 0085, 0087, 0091, 0097, 0099.
Each recipe binds its qualified T4 planning-source ID without reusing a T4 result as T5 evidence.
Exact/ambiguous/unknown-label/low-confidence probes cover selected schema/mapper behavior only.
Conflict separates selected-ASR provenance from explicit Raw-conflict schema preservation.
Adult-correction semantic execution stays HELD/UNMAPPED. Do not add adult/source fields or transfer
P2T4 follow-ups. Unknown-confidence rejection does not establish support for unknown confidence.

A1 non-orientation and fixture/fake-verifiable A2-A6 portions are authorized. All original mandatory
requirements remain in full Task 5. Orientation, A7/A8, stale-session, affected A4 proof, full A9,
and every unresolved semantic/downstream portion remain HELD/OPEN as applicable.
P2T4-FU-01 through FU-10 remain OPEN/unassigned. Security remains PENDING. C3/live phase/freeze/S14,
compute/model/image/secrets/budget/retention and separate execution gates stay unchanged; the
reviewed clauses do not make their unknown live state a precondition for this independent offline
slice. Baseline data/security/contract rules apply throughout.

### Approved paths, commands and contract locks

The following exact 13-file allowlist is approved; the separate canonical-approval append is
already recorded and is not an additional implementation path:

1. `backend/src/sketch2life/benchmark/feat018_p2_t5_evaluation.py`
2. `backend/tests/unit/test_feat018_p2_t5_evaluation.py`
3. `backend/tests/contract/test_feat018_p2_t5_manifest_contract.py`
4. `backend/tests/contract/test_live_image_demo_api.py`
5. `features/FEAT-018-live-image-canvas-flow/fixtures/feat018-p2-t5-evaluation-manifest-v1.json`
6. `features/FEAT-018-live-image-canvas-flow/evidence/metrics/P2_T5_OFFLINE_EVALUATION_20261022.json`
7. `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T5_OFFLINE_STATUS_20261022.txt`
8. `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T5_OFFLINE_EVALUATION_20261022.md`
9. `features/FEAT-018-live-image-canvas-flow/plan/P2_T5_EVALUATION_HARNESS_PLAN_DRAFT_20261021.md`
10. `features/FEAT-018-live-image-canvas-flow/CONTEXT.md`
11. `features/FEAT-018-live-image-canvas-flow/DECISIONS.md`
12. `features/FEAT-018-live-image-canvas-flow/status/STATUS.md`
13. `features/FEAT-018-live-image-canvas-flow/evidence/README.md`

Acceptance mapping, the exact commands, working directories and write effects are recorded in the
canonical issuance. Commands authorize the new runner/tests, selected existing regressions, Ruff,
mypy and repository validators, including security-validator read-only Git inventory.
Ordinary in-scope errors may be repaired and affected checks rerun; outside-scope findings must be
reported without editing their source. Scratch paths are confined to the approved ignored
`backend/.pytest-tmp-feat018-p2t5-*` directories and must be checked before any basetemp cleanup.

Consume-only source locks (whole defining-file SHA-256):
- VisionUnderstandingResultV2@2.0, `backend/src/sketch2life/contracts/schemas/vision_v2.py`:
  `BEA0511C400B452B86FF32A90CB5F65DF4C191A72A857B1024C30A65628CD0D8`.
- RawUnderstandingResultV1@1.0, `backend/src/sketch2life/contracts/schemas/raw_understanding.py`:
  `9A5350A7A6913C2FC4F9F3008AA3BCEBA652D90CD25F3CFE76F598B053A57E0B`.
- AsrResultV1@1.0, `backend/src/sketch2life/contracts/schemas/asr.py`:
  `1DCF8DB144EBFD080266F05B8E75AE404EC230EDC7983937A0E598E48C0B9B22`.
- Selected `application.ports.asr.AsrPort`:
  `92E9E68AA7C428A72CC366FF540F4D5F1BF3BFA2605AEC059B9DC20E9E84F9D6`.

The manifest/report record candidate-file digests alongside baseline HEAD. Live metrics remain
NOT_MEASURED and real provider execution remains NOT_EXECUTED. Evidence contains only IDs, hashes,
bounded status/count metadata and attribution; no raw media, prompt, transcript/model output,
header or secret. INTERNAL ERROR, HARNESS_INVALID, required skips and HELD are never PASS.
No runtime/schema/contract/dependency edits, provider/model/Modal calls, Git publication or Task 5
closure are authorized.

### Candidate execution snapshot - 2026-10-22

The bounded candidate is implemented; see `../evidence/notes/P2_T5_OFFLINE_EVALUATION_20261022.md`
for exact commands, hashes and limitations. Unit/manifest subset: 49 passed. Existing regressions:
162 passed, 5 intentional skips (no PASS credit). After the test-only socketpair guard correction,
the focused command on `.pytest-tmp-feat018-p2t5-http-r4` passed 56 tests; a subsequent run of the
entire `test_live_image_demo_api.py` module on fresh `.pytest-tmp-feat018-p2t5-http-r5` passed 30
tests. Counter scope is test-specific: invalid-media cases assert Vision/ASR/localizer zero; the
admitted-upload and rejected-implicit flow asserts Vision zero, then one injected Vision fake call
after explicit understanding (localizer zero; ASR is not injected there). This does not establish
live-provider behavior. The earlier collection error from missing `python-multipart`, the r3
socketpair-guard failure, and the offline wheel installation are preserved chronologically in the
evidence note; the wheel was not added to project dependencies. Post-correction Ruff and scoped
mypy both pass on the four approved Python files. After the test-only guard correction and latest
documentation synchronization, architecture, skeleton and repository-security validators returned
VALID; repository security scanned 2,596 publishable files and is not Security owner approval. The
repository-harness validator still returns HARNESS_INVALID for unrelated FEAT-045/046/047 missing
evidence directories; that result remains a failure, not a pass or waiver. Overall verification is
INCOMPLETE and all full Task 5 acceptance rows remain OPEN.

The CLI reports primary execution 100 SUCCEEDED / 20 NOT_EXECUTED and supplemental execution
21 SUCCEEDED / 5 NOT_EXECUTED. Successful subprobes in HELD cells do not resolve their requirements.
Full C0 and T5-A1..A9 remain OPEN as applicable. OSError/attempt-number proof, task-level
rate-limit/provider-error mapping, orientation, A7/A8, stale-session and unresolved downstream
portions remain HELD/UNMAPPED. Task 5 and FU-01..FU-10 stay OPEN/unassigned. Security PENDING and
all live gates remain inherited dispositions, not test findings. No final handoff review/commit,
provider/model/Modal execution or whole-task gate PASS is claimed.

## Person 2 remaining-gates disposition - 2026-10-22

Person 2 issued `W2_FEAT018_P2T5_REMAINING_GATES_DISPOSITION_01` in the coordinator chat; this is
a chat-relayed issuance, not an entry in `approvals/TASK_APPROVAL.md`, which was not changed under
the continuing APP hold. It preserves the existing bounded offline approval and assigns the
following statuses without expanding its scope:

- Orientation remains HELD and receives no A1 coverage; full A1 remains OPEN.
- A7 remains HELD; no mobile bundle build or scan is authorized or claimed.
- A8 remains HELD; no live smoke, provider, or Modal execution is authorized.
- Stale-session remains HELD/UNMAPPED; `STALE_CORRELATION` is not treated as stale-session.
- Rate-limit/provider-error may be characterized using the existing mapping only; task acceptance
  remains HELD/UNMAPPED.
- OSError/attempt-number proof remains HELD; no proof is claimed and no adapter fix is authorized.
- A9 remains OPEN; final handoff/closure requirements are not waived.

No item is assigned to `P2T4-FU-01..FU-10`, and no new owner or follow-up is created here. Any new
scope requires a separate disposition and approval. The disposition does not satisfy a gate, change
the existing bounded offline approval, or close Task 5. APP hold remains IN FORCE; Security remains
PENDING; full Task 5 remains OPEN.

## Historical reviewed source proposal - revision 0.9

The sections below preserve the pre-issuance proposal and its review chronology. Statements that
approval/paths/Git were pending describe that historical source. The current approval and D1-D4
above supersede those pre-issuance statements for the exact bounded offline slice only.

## 1. Purpose and authority

This plan turns the existing FEAT-018 P2-T5 task card into a staged evaluation-harness proposal.
It is a planning artifact only. It does not authorize code changes, test execution, provider/model
calls, Lightning or Modal use, credential/configuration changes, Git publication, or edits to
`approvals/TASK_APPROVAL.md`.

The existing task card describes fixture tests without network/model calls, an explicitly approved
live development run, sanitized evidence, and latency/schema/recapture/failure reporting. The
offline-first plan separates O4 pilot diagnostics from O5 producer connection and live completion.
This plan preserves that boundary: offline work and live work are separate gates, and a live run
cannot be inferred from an offline pass.

Claude's read-only review of revision 0.1 reported `MATCH` for SHA-256
`B09D9A7F7285AFCCBEBB6842779975840E039781ACBAFF2762936A6AA4505506` and verdict
`NEEDS CHANGES`. This revision clarifies the unambiguous boundary findings below and leaves owner
decisions explicitly open. The review reports one read-only `Get-FileHash` command, plus reads/grep;
it is not an approval or execution result. At that point the supplied task-source attachment
appeared to end after “- N”; that uncertainty is superseded by the 2026-10-22 direct user disposition
confirming `plan/PERSON_2_AI.md` is the complete and controlling P2-T5 source. No missing attachment
text is inferred or required for this plan.

Claude's read-only review of revision 0.2 reported `MATCH` for SHA-256
`D59352379A741EEE3D91E126212EC3C6564F67A3C1781EA245CB24290CDDE476` and verdict
`PASS WITH NOTES` with no blockers. This revision records the review's seven notes and makes
documentary clarifications where they do not require owner authority. Retry-policy compatibility,
offline-slice adoption, and all other owner/custodian/Security decisions remain OPEN/HELD. The review
was static only; it is not implementation approval, an execution result, or a grant.

Review-note disposition in this draft: (N1) retry assertions are scoped to the harness/timeout and
the existing retry-capable paths are disclosed for C0/owner disposition; (N2) offline-slice limits,
HELD semantics, A5/A7/A9 boundaries are explicit but adoption remains with Person 2; (N3) D3-R2
manifests are added to C0 inventory and the candidate filename is FEAT-018 namespaced; (N4) the
observed rate-limit code path is recorded, while task-level acceptance remains HELD/UNMAPPED
pending owner disposition; (N5) A7 requires a
bundle-capable scanner and otherwise remains HELD; (N6) credit evidence is identified as
owner-attested, and image-only is identified as this task's scope choice; (N7) the historical approval
entry date is corrected to 2026-09-12. None of these statements adopts an owner decision.

Claude's read-only review of revision 0.3 reported `MATCH` for SHA-256
`0C8A4174B1425302511D756E36F6FAC4D314DB1B29D07F954B40208E3729F9A2` and verdict `PASS` with no
blockers. It raised three non-blocking notes: explicitly state whether unresolved A4 rate-limit and
stale-session cases block A4; expand C0's retry-path inventory; and inspect mobile-app scripts for a
bundle scanner. This revision records those checks without resolving owner decisions. The review was
static only and is not an approval or execution grant.

Claude's read-only review of revision 0.4 reported `MATCH` for SHA-256
`FF517FDDC5BEBCC557792FCC08DD4D9F88B38F1A5256355701F9DAB1EBD7057F` and verdict `PASS` with no
blockers. Its first note was the revision label in §10.1; this revision corrects the label. Its
second note suggested two additional C0 leads:
`backend/src/sketch2life/contracts/schemas/vision_v2.py:483-487` and `lightning_client.py:359-372`.
They are added as source/configuration checks, not as claims about the selected live route. Its third
note leaves the contents of `apps/ui-mobile/scripts/` UNKNOWN; C0
already requires inspecting those scripts. This review was static only and is not approval or an
execution grant.

The user reports that Claude's read-only review of revision 0.6 returned `PASS WITH NOTES`, with no
blockers, for SHA-256
`AD70FF9306C3196A11A9B3FBF615D445AA86F5819068C3C122A1AF78A6173848`. This is a user-supplied
review result, not a repository evidence artifact or approval. Claude did not verify the current APP
state, Security disposition, current phase/freeze, or S14. The review applies only to revision 0.6;
it did not review revision 0.7 or this revision. User-supplied findings for rev 0.7 are recorded
below; they do not review this revision.

Revision 0.7 records the reported review notes as follows: the HTTP 429 and Vision V2 mapping are
documented in C0 while task fit remains HELD; the ASR-only mapping now cites `lightning_client.py`;
the duplicate legacy `AsrPort` is recorded; the Gate A/B constraint maps to T5-A2 and contract
documentation maps to T5-A9; timeout/retry/rate-limit/stale-session/provider-error evidence is
cross-referenced to acceptance rows; the manifest is described as 16 entries keyed by `fixture_id`;
and repo-static findings are separated from inherited owner/chat state. These edits do not close C0,
complete an acceptance row, or grant implementation/execution authority.

As explicitly clarified by the user, Claude's read-only review of revision 0.7 reported
`PASS WITH NOTES`, with no blockers, for SHA-256
`EB9BBA0E9A7121B4A20639BD6B1BB34E3A1A17328EB77CBE824E3BE488D82EEC`. Revision 0.8 recorded
findings N1-N7 and the static citation corrections and code/manifest observations below. Revision
0.9 corrects the recorded verdict only; the findings and all OPEN/HELD/UNKNOWN states are preserved.
This reported reviewer result is not implementation approval, execution authority, owner disposition,
or evidence for closing a gate. It does not verify APP, Security, phase/freeze, S14, branch, HEAD, or
worktree state. Revision 0.9 needs its own exact-hash read-only review.

P2-T4 was accepted as a diagnostic deliverable. Its 60 primary and 5 supplemental `UNRESOLVED`
results remain product gaps. On 2026-10-22, the user explicitly confirmed `P2T4-FU-01` through
`P2T4-FU-10` remain OPEN and unassigned, with none transferred to P2-T5.

On 2026-10-22, the user confirmed `plan/PERSON_2_AI.md` is the complete and controlling P2-T5 task
source, selected `sketch2life.contracts.schemas.asr.AsrResultV1@1.0` with
`sketch2life.application.ports.asr.AsrPort` for the P2-T5 ASR boundary, and adopted the bounded
offline scope in §2. This is a plan-scope disposition only. It does not authorize implementation,
test execution, provider/Modal use, Git activity, or Task 5 closure. APP hold `IN FORCE` and Security
`PENDING` are carried from owner/chat disposition, not verified against current APP or Security
records in this review.

## 2. Objective

Produce a reproducible, privacy-safe evaluation harness for the FEAT-018 image-understanding
boundary that:

1. exercises image admission, response-schema, provenance, malformed-output, and typed-failure
   behavior with synthetic fixtures and injected fakes, without network or model execution;
2. measures and records fixture coverage and rejection behavior without treating diagnostics as
   product eligibility or bypassing Gate A;
3. supports one separately authorized live development smoke run through backend-only
   infrastructure, using only an explicitly approved non-sensitive image and an explicitly pinned
   model/provider/configuration; and
4. produces evidence that is reproducible, redacted, attributable to a commit and execution
   environment, and independently reviewable.

The full P2-T5 task remains OPEN until all approved acceptance criteria, including the live gate
where required by the controlling approval, are met. If live authority is unavailable, only an
explicitly approved offline sub-slice may be reported complete; that does not close full P2-T5.

The adopted bounded offline slice includes the non-orientation portion of T5-A1 and only those parts
of T5-A2 through T5-A6 that can be verified entirely with synthetic fixtures or injected fakes,
without network or model execution. T5-A5 live-provenance evidence is excluded. T5-A7, T5-A8, and
T5-A9 remain outside this slice and OPEN. Orientation remains HELD. Rate-limit and stale-session
outcomes remain HELD/UNMAPPED. Any acceptance criterion that still contains a mandatory held,
excluded, or unverified requirement remains OPEN; a HELD item is never counted as satisfied. This
scope disposition does not authorize implementation or execution.

Within the adopted offline scope, timeout and other already-mapped typed failures may be exercised
with injected fakes. The existing rate-limit code path is documented in C0, but whether its mapping
satisfies the task is not decided; rate-limit and stale-session remain `UNMAPPED`/HELD pending owner
disposition. Those cases block T5-A4 completion if they remain mandatory in that criterion; their
HELD status is not a pass and no new error code or meaning is authorized.

## 3. Scope

### Included in the adopted bounded offline scope (plan disposition only)

- An offline fixture/evaluation harness for the image validator and FEAT-018 response boundary.
- Fixture/fake-verifiable portions of the synthetic cases for the 20 golden pilot activities, tied
  to their stable pilot IDs. Coverage is diagnostic only and does not imply model quality.
- Non-orientation image-admission cases: valid, corrupt, unsupported format, too large, too dark,
  blurred, and crop-risk. Orientation remains HELD; no EXIF reporting, rotation, or derivative is
  authorized by this disposition.
- Schema/provenance cases, including ASR present and ASR absent, with truthful modality state.
- Negative cases for prohibited fields, malformed output, missing provenance, source mismatch,
  and invalid claim/reference structure where supported by the currently approved contract.
- Injected failure cases only for mappings supported by existing typed boundaries. The harness adds
  no retry behavior; timeout tests preserve the applicable non-retryable/explicit-retry contract.
  Existing retry-capable paths are documented in C0, and this offline scope does not claim zero
  retries across all runtime paths. The observed rate-limit mapping and related session-version
  errors are documented in C0, but rate-limit task fit and stale-session mapping remain
  `UNMAPPED`/HELD; do not equate stale session with stale correlation.
- Sanitized offline evidence for coverage counts, schema outcomes, recapture outcomes, and typed
  failure counts. Live latency and provider/model/config evidence remain NOT MEASURED.

### Excluded unless separately planned and approved

- Changes to FEAT-003 contracts, schemas, prompts, adapters, validation, scoring, benchmark
  fixtures/runners, or producer connections.
- New public/runtime contracts, schema/catalog changes, eligibility decisions, Gate A/Gate B
  behavior changes, or automatic mapping/selection behavior.
- Changes to P1, mobile, shared integration, authentication/session wiring, or production
  deployment.
- Real child data, sensitive images, raw prompts/model outputs, authorization headers, secrets, or
  provider responses in committed evidence.
- Performance claims based on one smoke run. A smoke sample is not a benchmark.
- Any automatic assignment of P2-T4 follow-ups to P2-T5.
- Orientation behavior, T5-A7 mobile bundle scanning, T5-A8 live smoke, and T5-A9 handoff/closure.

T5-A7 remains HELD pending an approved bundle-capable scanner or suitable already-built artifact
and provenance. T5-A8 remains HELD pending current phase/freeze and Security/custodian disposition,
an exact compute/model/config route, an approved non-sensitive image, secret handling, bounded
sample/cost/time/retention limits, and a separate execution grant. T5-A9 remains OPEN. No live or
bundle-build work is authorized by this scope disposition.

## 4. Inputs and source boundaries

The controlling task card names FEAT-003 `VisionUnderstandingResultV2@2.0` as the consume-only input,
FEAT-018-owned `RawUnderstandingResultV1@1.0` as the output, and optional `AsrResultV1@1.0` as a
separately gated input. The user selected the exact P2-T5 ASR boundary as
`sketch2life.contracts.schemas.asr.AsrResultV1@1.0` with
`sketch2life.application.ports.asr.AsrPort`. The legacy same-named type in
`contracts.schemas.understanding` is not the selected P2-T5 ASR boundary. A duplicate `AsrPort`
definition also exists at `application.ports.understanding`, typed to that legacy contract; the
selected P2-T5 boundary remains the `contracts.schemas.asr` type and `application.ports.asr.AsrPort`.
The offline slice uses fixtures/fakes only and does not connect a provider ASR adapter. Preserve the
consume-only FEAT-003 boundary; no upstream schema or runtime change is authorized.
Before implementation, the owner/reviewer must also resolve the exact Qwen3-VL model
revision/configuration if it is a live acceptance criterion. Do not copy an upstream contract into
FEAT-018 under the same public name or silently change an upstream contract.

The 20-pilot synthetic fixture set and Task 4 diagnostics are inputs for coverage planning; their
results are not automatically evidence for a new Task 5 runtime or adapter behavior. Every reused
artifact must be explicitly mapped to a P2-T5 acceptance criterion, with source commit and tuple
where applicable.

Planning sources:

- `plan/PERSON_2_AI.md`, P2-T5 task card and required evidence/acceptance/DoD.
- `plan/P2_OFFLINE_FIRST_PLAN.md`, O4 offline completion, O5 producer/live completion, and the
  change-impact gate.
- `approvals/TASK_APPROVAL.md`, including the historical 2026-09-12 statement that P2-T3 through
  P2-T5 were separately gated, the later P2-T3/P2-T4 approvals, and the absence of a current
  P2-T5-specific implementation approval.
- `DECISIONS.md` and the P2-T4 diagnostics note, which keep Task 4 follow-ups OPEN and unassigned.
- `docs/context/SOURCE_REGISTER.md`, whose handbook entry is contextual only; the 2026-10-22 direct
  user disposition separately confirms `plan/PERSON_2_AI.md` is the complete and controlling P2-T5
  task source, without granting implementation authority.

## 5. Work packages and gates

### C0 — Scope, source, and path inventory

**Purpose:** convert this draft into a reviewable, bounded implementation proposal.

**Work:**

- The current scope prohibits Git operations, so branch, HEAD, and worktree state were not
  revalidated. The P2-T4 closure state was checked statically in its source records; this does not
  attest the current commit.
- Inspect the current validator, adapter, tests, contracts, fixture manifest, and evidence layout;
  identify existing behavior so the harness does not duplicate or mislabel Task 4 results.
- Inventory the existing D3-R2 image-admission artifacts, including
  `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/manifest-v1.json` and
  `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/evaluation-manifest-v1.json`.
  Compare their actual coverage before proposing new fixtures; a different directory alone does not
  justify a duplicate manifest.
- Inventory existing FEAT-003 `p2_t5_*` implementation/tests and existing media-validation/T4
  coverage. Keep FEAT-018 paths uniquely namespaced and do not reuse FEAT-003 code as FEAT-018
  evidence without a reviewed compatibility mapping.
- Produce an exact proposed changed-path list and map every path to an acceptance criterion.
- Record the user-selected ASR identity as
  `contracts.schemas.asr.AsrResultV1@1.0` through `application.ports.asr.AsrPort`. Before any
  implementation, bind each input contract by exact source revision/digest and preserve the
  consume-only FEAT-003 boundary. Any upstream change or producer connection stops for separate
  review.
- Build a 20-pilot × 6-category coverage matrix from `plan/ACTIVITY_PILOT_MATRIX.md`. For every
  cell, record the fixture ID, expected outcome, and whether it reuses a Task 4 case as a planning
  reference or needs a new Task 5 fixture. Task 4 JSON/results are not Task 5 results. `UNRESOLVED`
  and `EXPECTED_BLOCKED` remain diagnostic states; neither is a T5 test failure nor a satisfied
  product behavior.
- Record the 2026-10-22 disposition: orientation remains HELD; rate-limit and stale-session remain
  HELD/UNMAPPED. Do not omit mandatory criteria silently, invent semantics, or add error codes.
- Record the existing retry-capable boundaries found during review and whether the selected live
  route can reach them. C0 confirmed the source paths for these review-reported leads:
  `qwen_vision.py:398-401,1051-1063` (`_never_transient` and transient retry);
  `backend/src/sketch2life/contracts/schemas/vision_v2.py:483-487` (V2 retryability/attempt
  semantics); the
  `infrastructure/understanding/qwen3_vl_adapter.py:51-54` and corresponding
  `whisper_adapter.py:49-52` `max_retries` loops; `lightning_client.py:169-187,359-372,381`
  (`_post_with_retry`, its default, and the separate ASR-only error mapping); and
  `backend/src/sketch2life/interfaces/http/routers/live_understanding.py:74-79` (legacy V1
  `LightningVisionAdapter` construction only). The ASR-only `RATE_LIMITED` mapping is in
  `lightning_client.py:359-372`, not `live_understanding.py`. Also record `live_image_demo.py:1056`
  (`attempt_number`). The exact local Qwen/legacy adapter paths are not evidence that the configured
  external Lightning endpoint reaches them.
  Trace reachability through a future selected live route; grep presence alone does not prove a
  retry executes. Keep any live route HELD until its actual endpoint/retry behavior and compatibility
  with the applicable ADR are dispositioned; do not infer that a task grant can override an ADR.
- Pin the mobile bundle artifact identity/hash, build commit, bundle-capable scan command/tool
  version, and exact search patterns before claiming T5-A7. If no approved bundle-capable scanner or
  already-built artifact is available, keep A7 HELD; do not build a mobile artifact under this plan.
  Inspect `apps/ui-mobile` scripts as well as repository `tools/` when checking for an existing
  bundle-capable scanner. Record synthetic fixture generation provenance and distinguish it from
  model execution.
- Keep all P2-T4 follow-ups OPEN and unassigned; none transfers to P2-T5.
- Record the dispositions in §9. Keep unresolved path, review, APP, Security, and live gates open;
  obtain read-only review of this exact revision before any later implementation approval.

**Static findings — 2026-10-22 (read-only):**

- D3-R2 has two separate image-admission manifests. `manifest-v1.json` has 11 fixture entries;
  `evaluation-manifest-v1.json` has a `profiles` array with 16 entries, each carrying a unique
  `fixture_id` within that manifest. These IDs are scoped to their respective manifest paths, not a
  shared/global namespace; bind identity as `(manifest path, fixture_id)`. The manifests cover
  synthetic encoding, size, corruption, unsupported-format, and multi-frame cases; they are not a
  P2-T5 20-pilot × 6-category matrix. `backend/tests/unit/test_media_validation.py` separately
  exercises dark, blur, and framing reasons, but does not count provider calls.
- `tests/fixtures/feat018-p2-t4-mapping/manifest.v1.json` contains 20 P2-T4 pilot IDs and records
  `provider_execution: NOT_EXECUTED`; it is not P2-T5 execution evidence. The T5 manifest candidate
  does not exist.
- The three new FEAT-018 code/test path candidates in §9 do not exist. Existing generic
  `application/services/p2_t5_evaluation.py`, `contracts/schemas/p2_t5_evaluation.py`, and
  `test_p2_t5_evaluation*` paths are separate P2-T5 work and are not reused. The existing
  `backend/tests/contract/test_live_image_demo_api.py` has call counters for admitted-upload/no
  implicit call behavior, but its invalid-media 422 cases do not count provider calls.
- Two `AsrResultV1@1.0` definitions and two `AsrPort` definitions exist. FEAT-018 ports/services
  use `contracts.schemas.asr` and `application.ports.asr.AsrPort`; the legacy
  `contracts.schemas.understanding` result and `application.ports.understanding.AsrPort` are a
  separate boundary. The ASR V2-only `RATE_LIMITED` mapping is in
  `backend/src/sketch2life/infrastructure/ai/lightning_client.py:359-372` (not
  `live_understanding.py`): for a retryable 429 it returns `ASR_PROVIDER_FAILURE` /
  `TRANSIENT_RUNTIME_FAILURE`, preserves `retryable=True`, and builds `attempt_number=1`.
- The shared Lightning transport maps HTTP 429 to `RATE_LIMITED`, `retryable=True`
  (`backend/src/sketch2life/infrastructure/ai/lightning_client.py:114-117`). Vision V2 catches any
  `LightningProviderError` without preserving its provider code/retryability and maps it to
  `VISION_PROVIDER_FAILURE` / `PERMANENT_RUNTIME_FAILURE`, `retryable=False`
  (`backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py:159-167`). This differs from
  ASR V2's retryable transient mapping. These are statically observed adapter behaviors; whether
  either mapping satisfies the task remains undecided. Task-level rate-limit/provider-error mapping
  remains `HELD/UNMAPPED` pending owner disposition.
- The Vision V2 adapter's `OSError` branch supplies `TRANSIENT_RUNTIME_FAILURE` and
  `retryable=True` (`backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py:168-177`),
  while `_runtime_failure` sets `attempt_number=1` (`:258-281`). The contract validator permits only
  `attempt_number=2` for this transient detail
  (`backend/src/sketch2life/contracts/schemas/vision_v2.py:483-487`). Static inspection therefore
  indicates a possible constructor/contract mismatch; this has not been confirmed by execution.
  Keep C0 and T5-A4 OPEN/HELD pending owner disposition; do not change code or count it as evidence.
- The main `create_app` FEAT-018 path constructs `LightningVisionV2Adapter` and
  `LightningAsrV2Adapter`; each makes one HTTP request without a local retry loop. The V2 vision
  result contract permits attempt number 1 or 2 for specified outcomes. Historical owner approval
  allows at most two provider generations for one explicit `/v2/vision` request on schema/mapping
  failure, and a separate approval allows one semantic-empty repair where supported. These are
  historical behavior bounds, not a P2-T5 execution grant.
- Retry-capable legacy V1 adapters and the local Qwen adapter also exist. The legacy
  `live_understanding` router is not included by the current `create_app`; no evidence establishes
  that the current configured external Lightning endpoint reaches the local Qwen retry paths. The
  local transient classifier defaults to no transient retry, while explicit conditional retry paths
  remain in the adapter. Live route reachability stays UNKNOWN and A8 stays HELD.
- `backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py` is an existing inventory
  item. Its module docstring assigns one explicit transient retry to the existing Qwen adapter;
  `run_adapter_once` invokes the supplied adapter once under the cap and has no outer retry, while
  the generation layer performs one attempt and leaves retry choice to the adapter. This is a
  docstring/source description, not confirmation of selected-route behavior or execution authority.
- No bundle-capable scanner was found among `apps/ui-mobile/scripts/` or the name-matched tools
  under `tools/`; `tools/validate_repository_security.py` is not a mobile bundle artifact scan.

**C0 evidence-to-acceptance crosswalk (static source evidence only; not test coverage):**

| Evidence case | Repository evidence observed | Acceptance row(s) | Status / limit |
|---|---|---|---|
| Timeout | `lightning_vision_v2.py:150-158` maps timeout to `VISION_TIMEOUT` / `TIMEOUT_BUDGET_EXCEEDED`, non-retryable; `lightning_client.py:280-296` records the V2 ASR timeout mapping. | T5-A4; T5-A8 for any separately authorized live typed-failure evidence. | Static mapping only. Offline fake coverage remains proposed; A4 is OPEN while other mandatory failure cases are unresolved; A8 is HELD. |
| Retry | `lightning_client.py:169-187` has a bounded retry helper; retry-capable local Qwen/legacy paths are listed above. The selected live endpoint's reachability and behavior are UNKNOWN. | T5-A4; T5-A8. | Existing code paths are not harness evidence or a global no-retry guarantee. Route applicability and owner/ADR disposition remain OPEN/HELD. |
| Rate-limit/provider-error asymmetry | Transport maps HTTP 429 to `RATE_LIMITED`, `retryable=True`. ASR V2 maps it to `ASR_PROVIDER_FAILURE` / `TRANSIENT_RUNTIME_FAILURE`, preserving retryable; Vision V2 collapses any `LightningProviderError` (including rate-limit/provider-error) to `VISION_PROVIDER_FAILURE` / `PERMANENT_RUNTIME_FAILURE`, `retryable=False`. | T5-A4; T5-A8. | Static source mappings only; they differ across ASR/Vision. Task-level mapping remains `HELD/UNMAPPED` pending owner disposition. |
| Stale-session | Session code contains `STALE_SESSION_VERSION` / `STALE_SESSION_REVISION`, but no mapping from these outcomes to the selected P2-T5 understanding boundary was established. `STALE_CORRELATION` is a distinct contract value. | T5-A4; T5-A8 only if selected live evidence requires it. | `HELD/UNMAPPED`; do not count related session codes or stale correlation as coverage. |
| OSError/transient attempt mismatch | Vision V2 adapter's OSError path supplies `TRANSIENT_RUNTIME_FAILURE`, `retryable=True`, and `_runtime_failure` sets attempt 1; the schema validator allows only attempt 2 for that detail. | T5-A4. | Static discrepancy only; not confirmed by execution. Keep C0 and A4 OPEN/HELD pending owner disposition; no code change or coverage claim. |
| Provider-error | Shared transport emits typed `PROVIDER_ERROR`; Vision V2 collapses provider errors into a permanent Vision failure, while ASR V2 maps based on provider retryability. | T5-A4; T5-A8 for any separately authorized live typed-failure evidence. | Static mappings only; task-level mapping and selected-route applicability remain `HELD/UNMAPPED`/UNKNOWN. No fixture evidence has been run. |

The task-card requirement that observations cannot directly create Gate B or skip Gate A maps to
T5-A2; the required contract documentation maps to T5-A9. T5-A2 remains open pending the full
diagnostic matrix and boundary evidence. T5-A9 remains OPEN and outside the adopted offline slice.
Neither requirement is treated as covered by these static observations.

**C0 status:** Static source, fixture/path, and retry/live inventory and the evidence crosswalk are
recorded. C0 exit remains OPEN because the exact changed-path list is not approved, source
revision/digests still need binding, rate-limit/provider-error task mapping and stale-session mapping
remain HELD/UNMAPPED pending disposition, the Vision OSError/transient attempt-number discrepancy
requires owner disposition, and branch/HEAD/worktree were not checked under the no-Git scope. No test
or validator was run.

**Exit criteria:** exact scope, source tuples, paths, test commands, evidence destinations, and
non-goals are reviewed. These criteria are not yet met: the exact changed-path list remains
unapproved, contract digests are not yet bound, and branch/HEAD/worktree were not checked under the
no-Git scope. No implementation occurs during C0.

### C1 — Offline fixture harness

**Purpose:** validate deterministic behavior without network/model access.

**Proposed checks:**

- Run the image-admission cases with an injected fake/call counter and prove invalid/rejected images
  do not reach the provider boundary. Orientation remains HELD by the 2026-10-22 disposition; do not
  implement EXIF reporting, rotation, or an image derivative.
- Supply a complete 20 × 6 matrix: every pilot ID has exact, ambiguous, no-match, image/audio
  conflict, low/unknown confidence, and adult-correction cells. Each cell must point to a fixture
  and expected diagnostic/blocked outcome. A HELD cell is not coverage and blocks completion of A2.
  The adopted offline slice permits only A2 portions verifiable with fixtures/fakes; it does not
  report an incomplete matrix as full A2 completion. The Task 4 manifest/JSON can inform the matrix
  but is not Task 5 execution evidence.
  Task 4 `UNRESOLVED` and `EXPECTED_BLOCKED` labels remain diagnostic and are not failures or
  satisfied product behavior.
- Verify ASR-present and ASR-missing cases using
  `contracts.schemas.asr.AsrResultV1@1.0` / `application.ports.asr.AsrPort`; preserve truthful
  provenance and do not fabricate a transcript or aggregate confidence.
- Verify malformed and prohibited-field outputs fail closed and preserve typed failure semantics.
- Exercise only failure mappings that exist at the selected boundary, using injected fakes and
  asserting zero real provider/model calls. Timeout remains `NEVER_RETRY` and non-retryable; test
  that the harness performs no retry. Do not introduce retry behavior or new error codes. This
  assertion is scoped to the timeout contract and the harness, not all existing runtime paths.
  Existing retry-capable runtime paths are recorded as observed behavior, not changed or approved
  by this plan; their applicability to any live route remains for owner disposition.
  The observed rate-limit code path is recorded in C0, but its task-level acceptance mapping and
  the stale-session mapping remain `UNMAPPED`/HELD pending owner disposition;
  `STALE_CORRELATION` must not be treated as stale-session without an approved mapping. While either
  case remains HELD, A4 is incomplete if that case is in the adopted slice; only an explicit
  owner-approved bounded slice may exclude it.
- Verify observation output remains diagnostic/proposal data and cannot itself create Gate B,
  eligibility, or skip Gate A.

**Exit:** the owner-approved offline slice has all of its adopted acceptance items satisfied; no
HELD cell is counted as passing coverage. If rate-limit or stale-session cases remain in the adopted
slice but unmapped, A4 remains incomplete. Where the proposal explicitly excludes orientation,
unmapped A4 cases, mobile bundle scanning, or live work, the handoff labels those items OPEN/HELD and
does not call the affected criterion complete, T5-A1, A7, A8, or full A9 complete. Focused offline
tests, relevant regressions, and validators pass; evidence records synthetic fixture provenance,
counts, expected blocked outcomes, and zero-provider-call checks. Test commands and exact targets are
set at C0 and require implementation approval before execution. Passing this gate does not satisfy
the live criterion or close full P2-T5.

### C2 — Evidence and privacy controls

**Purpose:** make results reviewable without publishing sensitive source or provider data.

**Work:**

- Store evidence only inside `features/FEAT-018-live-image-canvas-flow/evidence/`.
- Record commit, environment/tool tuple, fixture/input identifiers, counts, hashes, redaction
  rules, and exact commands/results needed to reproduce the checks.
- Record how each synthetic fixture was generated and its stable pilot/source identifiers; state
  `provider_execution=NOT_EXECUTED` for offline results. Do not present fixture provenance as model
  provenance.
- Do not store raw images, raw prompts, raw model output, headers, tokens, or secrets. For a live
  run, store only approved non-sensitive input identity/hash and sanitized metadata.
- For the mobile bundle scan, bind the exact artifact name/hash, build commit, bundle-capable
  command/tool version, and search-pattern list before claiming a pass. A generic statement that an
  approved tool was used is insufficient. If no approved bundle-capable tool/artifact exists, record
  A7 as HELD; source-code architecture checks are not a substitute.
- Keep original fixtures and provenance; do not replace a source artifact with a derived result.

**Exit:** a reviewer can trace each metric to a sanitized input and result without access to secret
material; security checks are valid and tied to the candidate commit.

### C3 — Live-run readiness disposition (no execution)

**Purpose:** establish whether a live smoke is permitted and define its exact envelope.

Before a live run, obtain and record the current authority for all of the following:

- Security approval and the designated custodian's applicable disposition.
- Actual phase/freeze state, including any required early-route or S14 condition.
- Approved compute/provider route, region, resource profile, endpoint, and cost/time cap. ADR-0005
  names Lightning as development and Runpod as production; Modal is not an approved P2-T5 route in
  the current ADR. Any route change requires a new owner/Security disposition.
- Exact model revision, provider/config IDs, backend-only execution path, and permitted sample
  count.
- Explicit approval of the non-sensitive image and its handling/retention.
- Local secret delivery method; no token or endpoint secret in source, notebook output, evidence,
  mobile bundle, or command transcript.
- Stop conditions, no-automatic-retry handling, redaction, cleanup, and owner for the live run.
- Evidence for the 25-credit cap is owner-attested because the repository has no credit-metering
  interface; record the owner's pre/post balance or equivalent attestation and its basis. This is
  not machine-verified evidence.

ADR-0005's 2026-09-18 addendum is a narrow owner-run exception for synthetic/non-child FEAT-018
image tests, capped at 25 existing credits in total, with the owner manually initiating requests
and monitoring credits. It excludes audio/ASR, video, production inference, top-ups, and automatic
retries; Codex must not send live provider requests. Unclear call cost/balance means no call. This
exception is not a P2-T5 live grant and does not authorize Modal.

The later 2026-09-21 `TASK_APPROVAL.md` addendum separately permits an owner-run ASR smoke within
the same aggregate cap. P2-T5 deliberately proposes image-only scope; that is a task-scope choice,
not a claim that the later addendum forbids ASR. The selected live route must not trigger an existing
automatic-retry path under the current no-retry exception; if that cannot be established, live
execution remains HELD pending an applicable owner/Security policy disposition.

`APP hold IN FORCE` and `Security PENDING` are carried owner/chat planning-state facts, not verified
current repository state. They do not satisfy this gate. Modal account/kernel availability does not
itself establish an approved compute route or execution authority.

**Exit:** a separate, attributable live-execution grant binds the exact plan revision/hash,
changed paths, command/tool envelope, image, model/config, compute, sample limit, and stop rules.
Until then, live execution remains HELD.

### C4 — Bounded live development smoke (conditional)

**Purpose:** gather the task card's live evidence after C3 is approved.

**Run only under the separate C3 grant:**

- Use only the approved non-sensitive image, exact model revision, and backend-only route.
- Verify invalid image admission is rejected before provider invocation; do not use a live provider
  call to test invalid inputs.
- Record sample count beside latency p50/p95; label the result as a smoke, not a benchmark.
- Record schema outcome, recapture outcome, typed failures, provider/model/config IDs, and sanitized
  environment metadata.
- Stop on authority mismatch, unexpected data, redaction failure, scope drift, or any condition
  listed in the execution grant. No automatic retry or route substitution. A further request
  requires a separate explicit owner action and must still comply with ADR-0005; a task grant cannot
  override `NEVER_RETRY`.

Live execution is owner-initiated only under the existing ADR addenda. Codex may prepare and review
the envelope but must not send the provider request. The P2-T5 smoke is deliberately image-only;
ASR/audio is excluded by this task's proposed scope. Credit use within the 25-credit cap is
owner-attested, not measured by a repository tool. No live execution is authorized by this draft.

**Exit:** one valid, attributable, sanitized live result with no secret/raw-data leakage and with
  all stop conditions clear. If C3 is not approved or this run cannot be completed, record the
  blocker and keep the full P2-T5 task OPEN.

### C5 — Independent review and closure

**Work:**

- Reconcile plan, decision/status records, evidence index, fixture/results, and metrics.
- Bind all final gates to the exact handoff commit; do not treat missing, stale, partial, or invalid
  results as PASS.
- Obtain an independent final review of the exact handoff state.
- Record remaining product gaps and owners; do not mark P2-T4 follow-ups resolved or transferred
  without their own disposition.

**Exit:** every approved acceptance criterion is met, all evidence is attributable and sanitized,
independent review passes, and Person 2 records the closure disposition. Otherwise P2-T5 remains
OPEN (or only the explicitly approved offline sub-slice is reported complete).

## 6. Acceptance matrix

| ID | Acceptance criterion | Required evidence | Gate |
|---|---|---|---|
| T5-A1 | The image validator handles valid, corrupt, unsupported, oversized, too-dark, blurred, and crop-risk cases according to the pinned contract. Orientation remains HELD under the 2026-10-22 disposition; full A1 remains OPEN while the mandatory orientation requirement is unresolved. | Fixture matrix; typed outcomes; provider-call counter proves rejected inputs never reach provider; separate orientation disposition. | C0/C1 |
| T5-A2 | Every one of the 20 golden pilot IDs has all six O4 diagnostic categories: exact, ambiguous, no-match, image/audio conflict, low/unknown confidence, and adult correction. Observations remain diagnostic/proposal data and cannot directly create Gate B, create eligibility, or skip Gate A. A HELD cell is not satisfied coverage and blocks A2 completion unless an owner-approved bounded slice explicitly excludes it. | Complete 20 × 6 matrix with fixture ID, expected outcome, reuse/new status, and source mapping; evidence that observations cannot create Gate B or bypass Gate A. T4 results are planning references, not T5 pass evidence. | C0/C1 |
| T5-A3 | ASR-present and ASR-missing cases are truthful and preserve source/provenance. | Paired fixtures and assertions; no fabricated transcript/confidence. | C1 |
| T5-A4 | Malformed output and prohibited fields fail closed; injected failures map only to existing typed outcomes. The harness adds no retry behavior; timeout preserves `NEVER_RETRY`/non-retryable semantics. This does not assert zero retries across all existing runtime paths, which require owner disposition if reachable from a live route. Rate-limit/provider-error task mapping, stale-session mapping, and the OSError/transient attempt-number discrepancy remain HELD/UNMAPPED or unresolved; any mandatory item blocks A4 absent owner disposition. | Negative fixtures; boundary-to-code map; timeout and harness-specific retry assertions; observed retry-capable paths and their live-route applicability recorded; rate-limit/stale-session dispositions explicitly reported; OSError/transient discrepancy dispositioned before any claim of typed-failure coverage. HELD is not coverage. | C0/C1 |
| T5-A5 | Offline results bind to synthetic fixture/source hashes and state `provider_execution=NOT_EXECUTED`; live results, if separately authorized, bind to exact model/config provenance. | Sanitized evidence schema, fixture-generation provenance, and redaction check; no raw sensitive payloads. | C2/C4 |
| T5-A6 | Offline harness runs without network/model/provider access. | Exact command/output and zero-provider-call evidence tied to candidate commit. | C1 |
| T5-A7 | A specifically identified mobile bundle artifact contains no provider URL, token, or model credential. It remains HELD if an approved bundle-capable scanner or already-built artifact is unavailable; building a bundle is outside this draft. | Exact bundle artifact/hash, build commit, bundle-capable scan command/tool version, search patterns, and result. | C0/C2 |
| T5-A8 | One separately authorized, owner-initiated, image-only live smoke reaches the exact approved Qwen3-VL revision through backend-only infrastructure using the approved synthetic/non-child image. Image-only is this task's scope choice; no ASR/audio. A reachable automatic-retry path blocks execution under the current exception unless separately dispositioned. | Separate live grant; sanitized metadata; sample count; schema/recapture/typed-failure result; p50/p95 labeled smoke-only; owner-attested pre/post credit evidence within the ADR-0005 cap. | C3/C4 |
| T5-A9 | Full-task reports, contract documentation, and handoff records agree; remaining gaps and limits are explicit. An offline sub-slice may produce a separate labeled handoff but does not satisfy full A9 or close P2-T5. | Required contract documentation; final evidence index, commit-bound gate results, independent review, owner closure disposition; separate sub-slice evidence if adopted. | C5 |

## 7. Approval and execution boundaries

- This document is `DRAFT`; no implementation or test command is authorized by it.
- The current P2-T4 approval does not authorize P2-T5. A separate explicit P2-T5 approval is
  required before implementation.
- The owner/chat-carried `APP hold IN FORCE` means this draft does not modify
  `approvals/TASK_APPROVAL.md`; the current APP state and applicable document-approval route were
  not verified in this static review. Resolve the route before recording an approval there.
- The owner/chat-carried `Security PENDING` disposition blocks live execution. Current Security
  state was not verified here. C3 requires current evidence and a separate Security/custodian
  disposition; do not infer a release from prior task approvals or a running Modal kernel.
- Any changed path outside the approved list, any contract/provider/model/config change, or any
  scope expansion stops for review and new disposition.
- Run `python tools/validate_repository_security.py` before each future commit/push, as required by
  repository policy. This plan creation has not run validators or changed code.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| FEAT-018 P2-T5 is confused with FEAT-003 P2-T5. | Namespace all records and branch references as `FEAT-018 P2-T5` / `FEAT018-P2-T5`; use the FEAT-018 plan/approval only. |
| Task 4 gaps are silently treated as Task 5 scope. | Keep FU-01..FU-10 OPEN and unassigned until Person 2 explicitly maps any item into an approved Task 5 revision. |
| Offline tests are presented as live/model evidence. | Separate C1/C2 from C3/C4; label live metrics NOT_MEASURED until an authorized live run completes. |
| Existing upstream contracts or runtime are changed accidentally. | C0 path inventory and source/version binding; separate review/approval for every FEAT-003 or shared-contract effect. |
| Sensitive images, prompts, outputs, or credentials enter evidence. | Use synthetic fixtures offline, one explicitly approved non-sensitive live image, local secret delivery, redaction checks, and feature-local sanitized evidence. |
| A single smoke is overstated as performance evidence. | Record sample count beside p50/p95 and describe the run as smoke only; require a separately designed benchmark for performance claims. |
| Current phase/freeze or compute authority is unknown. | Keep live execution HELD until C3 has current, attributable owner/custodian/Security dispositions. |

## 9. Recorded disposition and remaining gates

### User disposition — 2026-10-22

- `plan/PERSON_2_AI.md` is the complete and controlling task source for P2-T5. No missing
  attachment tail is required or reconstructed.
- The P2-T5 ASR boundary is `contracts.schemas.asr.AsrResultV1@1.0` through
  `application.ports.asr.AsrPort`. The duplicate legacy `contracts.schemas.understanding.AsrResultV1`
  is not selected for this task.
- Adopt a bounded offline slice: the non-orientation portion of A1, plus only A2-A6 requirements
  verifiable with fixtures/fakes offline. Orientation, A7, A8, rate-limit, and stale-session remain
  HELD/UNMAPPED. A criterion with any mandatory held or excluded item remains OPEN. Full Task 5 and
  FU-01..FU-10 remain OPEN; no FU is assigned to Task 5.
- This disposition finalizes scope only. It does not authorize implementation, tests, provider or
  Modal calls, Git, or Task 5 closure. APP hold `IN FORCE` and Security `PENDING` are inherited
  owner/chat dispositions, not states independently verified against current repository records in
  this review.

### State provenance — repository-verified vs. carried

- Repository-static findings in this revision include the source/task text, fixture manifest
  entries, code paths and mappings, duplicate ASR boundary definitions, and the plan's DRAFT label.
  They are source observations, not executed test coverage or gate PASS results.
- The complete-task-source confirmation, selected ASR boundary, bounded offline-slice disposition,
  APP hold `IN FORCE`, and Security `PENDING` are carried from the user's owner/chat disposition.
  This review did not independently verify the current APP record or current Security disposition.
- Current phase/freeze and S14 state remain UNKNOWN. Claude's revision 0.6 review did not verify
  them, and this plan-only update does not establish them. Current APP/Security records were not
  rechecked for this revision; APP hold and Security status remain owner/chat-carried only.
- Branch, HEAD, and worktree remain unverified because this scope prohibits Git. The branch and
  baseline recorded at the top of the plan are historical values, not current-state evidence.
- The reported Claude results for revisions 0.6 and 0.7, including findings N1-N7, apply only to
  their stated hashes; neither is a review result or approval for revision 0.9 or gate-closure evidence.

### Remaining gates before implementation approval

1. The exact changed-path list and each path-to-acceptance mapping remain PROPOSED. C0 inspected the
   current path inventory, D3-R2 manifests, existing FEAT-003 `p2_t5_*` names, and media/API tests;
   none of the proposed new FEAT-018 paths is approved for implementation. Do not mistake generic
   FEAT-003 files or P2-T4 evidence for P2-T5 outputs.
2. Bind the exact source revision/digest for each consumed contract before implementation. Preserve
   FEAT-003 `VisionUnderstandingResultV2@2.0` as consume-only and FEAT-018-owned
   `RawUnderstandingResultV1@1.0`; do not change upstream schemas or runtime.
3. Orientation behavior remains unresolved and HELD. The HTTP 429 and Vision/ASR adapter mappings
   are repo-observed, but rate-limit task fit remains HELD/UNMAPPED pending owner disposition;
   stale-session remains UNMAPPED/HELD. If either is mandatory in A4, A4 remains OPEN. Do not add a
   new code or equate stale session with stale correlation. Existing retry-capable paths and their
   possible live reachability remain disclosed; this plan makes no global zero-retry claim.
4. A7 remains HELD: no approved bundle-capable scanner or suitable artifact/provenance is bound.
5. A8 remains HELD: current phase/freeze and S14 state are UNKNOWN; Security/custodian disposition,
   compute route, model/config, approved non-sensitive image, secret handling,
   sample/cost/time/retention limits, and a separate execution grant are not established. Security
   `PENDING` is inherited from owner/chat and was not independently verified in this review. Modal
   is not authorized by ADR-0005.
6. The applicable APP/document-approval route is UNKNOWN; APP hold `IN FORCE` is carried from
   owner/chat and was not independently verified here. No P2-T5 implementation approval is
   recorded in the carried planning state; `approvals/TASK_APPROVAL.md` remains untouched.
7. Claude reported `PASS WITH NOTES`, with no blockers, for revision 0.7 hash
   `EB9BBA0E9A7121B4A20639BD6B1BB34E3A1A17328EB77CBE824E3BE488D82EEC`, as explicitly clarified
   by the user. Findings N1-N7 remain recorded. This reviewer result is not implementation approval,
   execution authority, owner disposition, or gate-closure evidence. Obtain a new read-only review
   bound to revision 0.9's exact SHA-256 before any later plan approval.
8. T5-A9 remains OPEN and outside the adopted slice. Any other mandatory acceptance portion not
   implemented and evidenced under a later separate authorization remains OPEN.

### Proposed path candidates — not approved

These candidates were statically inventoried at C0. Their presence/absence and current coverage were
checked, but the paths remain unapproved for implementation and require a separate exact path
disposition:

- `backend/src/sketch2life/benchmark/feat018_p2_t5_evaluation.py`
- `backend/tests/unit/test_feat018_p2_t5_evaluation.py`
- `backend/tests/contract/test_feat018_p2_t5_manifest_contract.py`
- `backend/tests/contract/test_live_image_demo_api.py` exists. Current assertions cover zero calls
  for an admitted upload before explicit understanding and for rejected implicit execution, but do
  not count calls on rejected invalid-media uploads. Extend this existing path only if that specific
  zero-provider criterion is included and the path is later approved.
- `features/FEAT-018-live-image-canvas-flow/fixtures/feat018-p2-t5-evaluation-manifest-v1.json`
  (candidate only; C0 compared it against D3-R2 manifests and FEAT-003 names, but it remains
  unapproved).
- A feature-local offline metrics file and evidence note under
  `features/FEAT-018-live-image-canvas-flow/evidence/` (exact filenames set at C0).
- After approval, scoped updates to this plan, `CONTEXT.md`, `DECISIONS.md`,
  `status/STATUS.md`, and `evidence/README.md` as needed for the approved slice.

The user scope dispositions above remain recorded in revision 0.9. The remaining gates and exact
paths are still unresolved; implementation and live execution remain NOT AUTHORIZED.

## 10. Proposed sequence

1. Obtain Claude's read-only review of revision 0.9, bound to its exact SHA-256.
2. Resolve the exact implementation/evidence path list and bind each path to the approved offline
   acceptance portions; keep every unapproved path proposed only.
3. Resolve the applicable APP/document-approval route and receive a separate implementation
   approval for a pinned plan revision. The current disposition is not that approval.
4. Implement and run C1/C2 only after separate authorization; review offline results. No such work
   is authorized by revision 0.9.
5. Keep A7/A8 HELD until their scanner/artifact and live-specific gates are separately satisfied.
6. If live evidence remains required, obtain a separate live-run grant before any owner-run request;
   do not substitute another route or expand sample scope.
7. Complete remaining mandatory criteria, obtain independent final review, and request Person 2's
   closure disposition. Full Task 5 remains OPEN until then.
