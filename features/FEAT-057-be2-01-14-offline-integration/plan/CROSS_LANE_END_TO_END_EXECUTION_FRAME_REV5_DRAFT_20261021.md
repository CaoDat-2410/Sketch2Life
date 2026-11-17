# BE2-01–14 full cross-lane integration frame — revision 5 draft

- Status: `DRAFT / REV4_RE-REVIEW_P3_NOTES_ADDRESSED_IN_DRAFT / READY_FOR_RE-REVIEW / NOT_IMPLEMENTATION_APPROVAL`.
- Date: 2026-10-21 (Asia/Saigon).
- Parent (preserved unchanged): `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV4_DRAFT_20261021.md`, SHA256 `6E5147209C01750E65E6E26BC6D8D237BAD625AFF0087AD1F88FBDE0D6F0DB3F`, 92,728 bytes; its manifest `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV4_20261021.json`, SHA256 `264A3C754DFD9B6A4BF93787414701E11F5A053E7CC94FFF638054EC23BB5C89`, 29,003 bytes, is also preserved.
- Grandparent (preserved unchanged): `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV3_DRAFT_20261021.md`, SHA256 `6F8703F09D98171171447C9592C3CAB137B7DB142E877CA152ACD61E2B3DC653`, 88,836 bytes; its manifest `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV3_20261021.json`, SHA256 `62BD19A1BDE16201F35F57613E0790D2B75455DD2E61F4ADBC2A713BD9FD5C3E`, 26,748 bytes, is also preserved.
- Earlier ancestor, revision 2 (preserved unchanged): `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_REV2_DRAFT_20261021.md`, SHA256 `E0AE164BF8F6193E331B3F6965A7200E10069A1B05FA568FD40838C3E2A19A5F`, 54,996 bytes; its manifest `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV2_20261021.json`, SHA256 `6DED7773187D95B5C2CDA39C5C6FCC1DA2629B007A54C98F969DC5F834E9A569`, 23,080 bytes, is also preserved.
- Earlier ancestor, revision 1 (preserved unchanged): `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_DRAFT_20261021.md`, SHA256 `1B17056637542C78342076C050E46C55666DE21F2AC562CCCBD2D7F48406C2FD`, 21,759 bytes; its manifest `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_20261021.json`, SHA256 `9B6DECC3D37A9183333A5F7F731D5DE01EBF0BA4B235AF774A8C3E1E9129746A`, is also preserved.
- Review input: independent review 1, verdict `CHANGES_REQUIRED` (0 P1 / 5 P2 / 8 P3), preserved at `evidence/notes/CROSS_LANE_END_TO_END_FRAME_REVIEW1_REPORT_20261021.md`, SHA256 `9127C052A2B37F789B2142CDB0813ACFC1D4134D82B1E0D0F193C5F791798843`. The disposition of every review-1 finding stays in §9.1.
- Review input 2: independent re-review of revision 2, verdict `PASS_WITH_NOTES` (as named in the owner's instruction for this revision), with nine P3 notes N1–N9. The report file is not in this worktree, so it is not hash-pinned; the notes are recorded as relayed and their disposition is in §9.2. `PASS_WITH_NOTES` is a document-review result. It is not approval of any code, schema or test.
- Review input 3: read-only re-review of revision 3, verdict `PASS_WITH_NOTES`, no P1, no P2 and three P3 notes. It was run in the session that wrote revision 3, so it is not an independent cold read, and its report was given in chat and not saved as a repository file. It is therefore not hash-pinned; its notes are recorded as stated and their disposition is in §9.3.
- Review input 4: read-only re-review of revision 4 run in a separate session, verdict `PASS_WITH_NOTES`, no P1, no P2 and four P3 notes. Its report is in that session's transcript and was not saved as a repository file, so it is not hash-pinned; the notes are recorded as stated and their disposition is in §9.4.
- Candidate worktree: `.worktrees/be2-01-14-integration-linked`.
- Candidate branch/HEAD observed: `feature/be2-backend-ai-integration` / `1649b72978877d82b4d7662040ff3555dee0a3a7`.
- Worktree at successor start: 154 dirty paths by `git status --porcelain -uall` (the 152 at revision 4 start plus the revision-4 plan and manifest; those 152 were the 150 at revision 3 start plus the revision-3 plan and manifest; revision 3 started with 136 entries without `-uall`, which collapses untracked folders), staged 0. Revision 2 started at 147; the differences are not itemised here and are left to the G0 read-only snapshot. This frame does not assume those local edits exist at HEAD or in a remote branch.
- Input manifest: `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV5_20261021.json` (created after this frame; it pins this frame and the exact planning and source inputs).

This revision corrects the parent's text only and adds two tables: the disposition of the revision-4 notes (§9.4) and a provenance table for the §6.1 paths. The revision-3 disposition (§9.3) was added in revision 4; the status ladder (§1.4), the boundary scope table with its approval reference (§6.1) and the two acceptance tiers (§6.2) in revision 3. Addressing a note in this draft does not close any gate: every owner adoption, decision or approval named below stays pending or blocked until it is recorded in its owning feature record. This revision changes no state: X01 `PARTIAL`, X05d `BLOCKED`, X05c/CR09-02 `OPEN`, X09-08 `NOT_IMPLEMENTED`, and D4, budget unit/limit/max-hold/deadline, phase S and reservation expiry/renewal stay pending.

## 1. Goal and authority

Build and verify the complete **behavioral graph** between BE2-01–07 and BE2-08–14 using owner-approved public contracts, producer-created values, and consumer-observed state. The final BE2 handoff should give the BE1 integrator a clean, reviewable snapshot and stable seams to adopt. Git branch ancestry by itself is not integration evidence.

The approved FEAT-057 integration plan revision 2 authorizes offline, FEAT-057-owned composition/adapters/tests, but requires an edge to remain `NOT_IMPLEMENTED` when its card-owned contract or adoption is missing. It excludes editing card-owned contracts/migrations, shared database provisioning, live routes, providers, Lightning, commit/push/merge, and card acceptance changes. This frame organizes the full work; it does not expand that approval. Card-owned changes need reviewed, exact scopes and supplemental approvals in their own feature records. FEAT-057 owns only the cross-lane composition layer and its evidence.

### 1.1 Card-to-feature directory map

Several administrative FEAT numbers are shared by two cards (`artifacts/FEATURE_ID_COLLISION_MAP.md`). This frame always names the full directory.

| Card | Owning feature directory |
|---|---|
| BE2-01 job foundation | `FEAT-044-be2-ai-job-foundation` |
| BE2-02 vision correction | `FEAT-048-be2-vision-correction` |
| BE2-03 assistance orchestration | `FEAT-049-be2-assistance-orchestration` |
| BE2-04 sketch generation | `FEAT-050-be2-sketch-generation` |
| BE2-07 knowledge script | `FEAT-056-be2-knowledge-script` |
| BE2-08 knowledge video | `FEAT-050-be2-knowledge-video` |
| BE2-09 video review/playback | `FEAT-051-be2-video-review-playback` |
| BE2-10 video failure disposition | `FEAT-052-be2-video-failure-disposition` |
| BE2-11 activity execution | `FEAT-053-be2-activity-execution` |
| BE2-12 content publication | `FEAT-048-be2-content-publication` |
| BE2-13 preset automation | `FEAT-054-be2-preset-automation` |
| BE2-14 AI policy | `FEAT-049-be2-ai-policy` |
| Integration composition | `FEAT-057-be2-01-14-offline-integration` |

### 1.2 Owner design directions (not implementation approval)

These are recorded owner design directions. They are not reopened here, and none of them is an approval to change code, schema or tests.

- D1: BE2-01 alone opens/commits/rolls back the paired lifecycle UoW; BE2-08 is a row-limited participant. Retry, timeout, cancel, reconciler and outbox lifecycle changes must not bypass the job/run pair. The **selected** lock order is job → run → source fences. D1 itself requires it to be checked against every actual lock path; that review is still pending (§4.3). D1 also states that adding boundaries S and F still needs review and a separate supplemental approval.
- D2: `VideoRun.attempt_id` is bound at committed start S and cleared on retry; the video-owned terminal stale state is distinct from budget waiting.
- D3 C1-A: budget deferral is durable BE2-01-owned metadata; job and run both remain `QUEUED`; no new job/video budget state. Wait time is excluded from dispatch-loss and retry recovery. Resume rechecks eligibility and reservation. Numeric bounds and deadline action remain pending.
- D3 C2-A: B-stale writes the authoritative stale outcome, receipt, paired terminal stale run without artifact/ready state, and verified-owned-ref keep-private intent in one commit. BE1 artifact adoption and accepted-reference protection remain required.
- X01/X05 owner dispositions (`evidence/notes/OWNER_DISPOSITION_X01_X05_20261021.md`) and G0 B1–B7 (`evidence/notes/G0_CARD_OWNER_DECISION_BALLOT_20261021.md`): contract direction only. B6/X05d is `BLOCKED`; OD-X05c is open.

The D4 decision for `BUDGET_EXCEEDED` **after provider work has completed** is still pending. Do not infer cancellation, acceptance, quarantine, refund, settlement, retry, or rerun. `X05c/CR09-02` remains open and `X05d` remains blocked. No design review, draft, or offline pass substitutes for implementation approval or per-card acceptance.

### 1.3 Existing exact-hash card approvals are historical

The owner approved five card scope addenda at exact hashes. Those approvals still govern only their own bytes:

| Card | Approved addendum | SHA256 | Implementation state |
|---|---|---|---|
| BE2-01 | `FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_BE2_01_SCOPE_DRAFT_20261021.md` | `AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD` | Typed-route execution subset implemented in this worktree, uncommitted (§6, G0). It covers the typed route only; no foundation-side change for A, S, H, B-accepted, B-stale, F or F-reject is approved (§6.1). |
| BE2-07 | `FEAT-056-be2-knowledge-script/plan/CROSS_LANE_BE2_07_SCOPE_DRAFT_20261021.md` | `CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24` | Not started; no durable fence in the approved boundary. |
| BE2-08 | `FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md` | `6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0` | Not started. |
| BE2-09 | `FEAT-051-be2-video-review-playback/plan/CROSS_LANE_BE2_09_SCOPE_DRAFT_20261021.md` | `121699BE6A3134C65EF16917941FA75F00401EA18462BA929C2E897BCAB46285` | Not started; X05d blocked. |
| BE2-14 | `FEAT-049-be2-ai-policy/plan/CROSS_LANE_BE2_14_SCOPE_DRAFT_20261021.md` | `417A740BA60E624BE2AA78D861E8DAEF80094AAF9992C3E65E782EB7EA78C9D8` | Not started. |

These approvals are historical relative to the later candidate drafts (BE2-01 foundation Rev7, BE2-08 Rev3, BE2-14 Rev3 and the CRs). They do **not** cover the expanded source, schema, codec, receipt or projection paths in those drafts (see slice plan Rev8 §2). Boundaries A, S and F, the hold, B-accepted, B-stale, F-reject and every new schema need independent review and a separate supplemental approval in their owning records before any edit. No such supplemental approval exists today on the BE2-01 side for any of them, because BE2-01's only supplemental approval is the typed route. The BE2-07, BE2-08, BE2-09 and BE2-14 addenda are hash-bound but have no recorded execution manifest, and A and B-accepted also lack an adopted shared-UoW entrypoint (CR08-01) (§4.1, §6.1).

The BE2-07/08/09/14 approvals are bound to their addendum hashes. Each addendum lists *candidate* allowed files, and each approval says the exact execution file subset must be recorded before editing. `evidence/notes/APPROVED_SCOPE_EXECUTION_MANIFEST_20261021.md` freezes only the three BE2-01 typed-route paths; for the other four cards it records that no source or test path is frozen. A candidate file list in an addendum is therefore not a recorded execution subset, and none of these four cards has one.

### 1.4 Status ladder

Five different things are easy to blur. This table keeps them apart for each boundary or gate. `none` means no such record exists; it is not a pending approval. Source for every cell: the cited drafts, the approval files in §6.1 and the source facts in §3–§5.

| Item | Candidate design | Owner direction | Adopted contract | Implementation approval | Implementation |
|---|---|---|---|---|---|
| A — submit | Foundation Rev7 §4, BE2-08 Rev3, CR08-01 (`OPEN_CANDIDATE`) | D1 (BE2-01 owns the UoW) | none; §4.4 prerequisites open | none for the BE2-01 side; BE2-08 addendum is hash-bound with no execution manifest | `NOT_IMPLEMENTED` |
| S — start | Rev7 §4, Budget CR Rev2 §3, BE2-08 Rev3 | D1 (S needs review and separate approval), D2 (attempt bound at S) | none | none; no worker/provider execution authorization exists | `NOT_IMPLEMENTED` (the typed route is broker-level only) |
| H — hold / resume | Budget CR Rev2, budget schema CR | D3 C1-A | none; bound, deadline action and reservation expiry/renewal pending | none; a schema change needs its own scope | `NOT_IMPLEMENTED` |
| B-accepted | Rev7 §4/§10, BE2-08 Rev3 | D1 | none | none for the BE2-01 side; BE2-07 and BE2-08 addenda hash-bound, no execution manifest | foundation-only completion exists in source; the paired boundary is `NOT_IMPLEMENTED` |
| B-stale | Stale CR Rev2, BE2-08 Rev3 §4 | D2, D3 C2-A | none; BE1 packet `NOT_SENT` | none | `NOT_IMPLEMENTED`; source has no stale video state (§4.2) |
| F — failure / retry / timeout / cancel | Rev7 §4 | D1 | none | none | foundation-side recovery exists unpaired; the paired boundary is `NOT_IMPLEMENTED` |
| F-reject | Rev7 §3–§4 | D1 (separate reject UoW) | none | none | rejection is committed inside `accept_completion` today; the separate boundary is `NOT_IMPLEMENTED` |
| Guard / I | Rev7 §3 | D1; NEW-5 owner confirmation of I still pending | existing source behavior; no new contract proposed | none needed for existing behavior | exists in foundation source, unchanged |
| Typed route (X09-08, route level) | BE2-01 addendum | none required | hash-bound addendum | APPROVED, three exact paths | implemented, uncommitted; does not close X09-08 |
| X05d resolver/fence | none identified | OD-X05d / G0 B6: `BLOCKED` | none | none | `BLOCKED` |
| D4 completion-time `BUDGET_EXCEEDED` | D4 ballot draft | pending | none | none | not classified; nothing inferred |

### 1.5 What this plan does not claim about approvals

- A `PASS_WITH_NOTES` from either review is a document-review result. It does not approve code, schema, tests or any boundary.
- The BE2-02, BE2-11, BE2-12 and BE2-13 approval records are not pinned by the manifest and this plan makes no claim about their approval state. The manifest pins their plans (BE2-11/12/13 `PLAN.md`; the BE2-02 C2 typed-context plan) and the BE2-03/04/10 approval records, not the BE2-02/11/12/13 approvals. Any statement about those four approvals needs the records pinned first.
- FEAT-057 may build composition, adapters and tests only inside paths its own approval covers (`backend/src/sketch2life/infrastructure/cross_lane/`, `backend/tests/integration/be2_cross_lane/` and FEAT-057 records), and only against contracts the owning cards have already adopted. It stops when a contract is missing and leaves the edge `NOT_IMPLEMENTED`.

## 2. One graph, not one artificial chain

```mermaid
flowchart LR
  K07[BE2-07 exact source] -->|X01| V08[BE2-08 generation worker]
  P12[BE2-12 published content] -->|X03| V08
  K07 -. invalidation X02 .-> R09[BE2-09 review/playback]
  K07 -. X05d current-source resolver/fence, BLOCKED .-> R09
  P12 -->|X04| R09
  P12 -->|X04| A11[BE2-11 activity]
  P13[BE2-13 preset intent] -->|X07| J01[BE2-01 job foundation]
  Policy14[BE2-14 eligibility / execution / budget] -->|X08| Consumers[BE2-03 / 04 / 08 / 13]
  J01 -->|X09 job + attempt| C02[BE2-02]
  J01 -->|X09 job + attempt| C03[BE2-03]
  J01 -->|X09 job + attempt| C04[BE2-04]
  J01 -->|X09 job + attempt| V08
  J01 -->|A/S/H/B/F lifecycle UoW| V08
  V08 -->|X05 exact finalized artifact| R09
  V08 -->|X06 typed exhausted failure| F10[BE2-10 disposition]
```

The main generation path is `exact source/publication + explicit intent → BE2-01 submission A → policy/hold → committed start S → BE2-08 execution → one authoritative completion boundary`. It then branches to accepted artifact (`B-accepted`), context-stale output (`B-stale`), failure/retry (`F`), or business rejection (`F-reject`). External generation is between S and completion; no database transaction spans provider work. Publication, invalidation, presets and failure disposition are separate graph edges, not steps every job must traverse. X02 and X05d are drawn separately on purpose: X02 does not substitute for X05d (§3.1).

## 3. Current edge ledger and target proof

Every edge uses the real producer service and the consumer's public, versioned contract. A fixture may replace an unavailable external owner, queue or provider only; it may not manufacture producer output, bypass a fence, write another card's repository, or turn a candidate contract into an adopted one.

| Edge | Current state | Owner-to-owner proof required for the full frame | Primary card owners |
|---|---|---|---|
| X01: BE2-07 source → BE2-08 generation | `PARTIAL` | Resolve exact source pin; preserve version/hash/audience/context; fence invalidation through BE2-08 finalization on the same durable UoW/store. Both invalidation-vs-finalize winner orders must be tested. | BE2-07, BE2-01, BE2-08 |
| X02: BE2-07 invalidation → BE2-09 | `NOT_IMPLEMENTED` | Deliver an authentic invalidation to the exact dependent review/playback target; deduplicate replay. Needs its own owner decision, card scope and supplemental approval (OD-X05d). It is not a way to satisfy X05d. | BE2-07, BE2-09 |
| X03: BE2-12 publication → BE2-08 | `NOT_IMPLEMENTED` | Resolve producer-created published content by exact id/version/hash/audience; draft/recalled/superseded/unauthorized content is denied before A/S/provider. | BE2-12, BE2-08, BE2-01 |
| X04: BE2-12 publication → BE2-09/11 | `NOT_IMPLEMENTED` | Each consumer independently resolves the exact published version through a public contract; recall/audience/authority changes block the consumer's commit/action. | BE2-12, BE2-09, BE2-11 |
| X05: BE2-08 output → BE2-09 | `NOT_IMPLEMENTED`; X05d `BLOCKED`; X05c/CR09-02 `OPEN` | Sub-edges X05a–X05d in §3.1. All four must pass before X05 can pass. | BE2-01, BE2-08, BE2-09, BE2-07 (X05d) |
| X06: BE2-08 failure → BE2-10 | `NOT_IMPLEMENTED` | Authoritative exhausted failure reaches the exact `FailureTarget` through a typed, replayable receipt; Teacher retry/skip/end is explicit and idempotent; late success cannot defeat a terminal decision. | BE2-01, BE2-08, BE2-10 |
| X07: BE2-13 preset → BE2-01 job | `NOT_IMPLEMENTED` | Explicit immutable preset dispatch creates/deduplicates one correctly scoped job after policy and disable-generation checks; BE1 session compare-and-apply ownership is respected. | BE2-13, BE2-01, BE2-14; BE1 session owner |
| X08: BE2-14 policy → BE2-03/04/08/13 | `NOT_IMPLEMENTED` | Each consumer binds an adopted phase-specific eligibility decision; execution authorization and budget reservation are separate (§5.1); deny/defer stops side effects; missing authority fails closed. | BE2-14 plus each consumer owner |
| X09: BE2-01 job/attempt → BE2-02/03/04/08/13 | `NOT_IMPLEMENTED`; **X09-08 `NOT_IMPLEMENTED`** (§3.2) | Persisted job → run → source/preset pin → registered handler → committed S → completion receipt; preserve job/attempt/subject/idempotency lineage; unsupported type never reaches a provider and has a defined lifecycle outcome. | BE2-01 and each handler owner |

Existing BE2-03→04→05→06 offline chain evidence is a regression baseline, not a substitute for these edges. The current 14 X01 tests, 282 adjacent BE2-07/08 tests and Modal 296/296 selected-package receipt remain bounded evidence only; they do not change the ledger above. A skipped, unapproved, unavailable, or unimplemented edge is never counted as PASS.

### 3.1 X05 sub-edges, X05d and the X02 boundary

| Sub-edge | Meaning | Current state and gate |
|---|---|---|
| X05a | Two separate foundation-owned atomic boundaries: submission A and finalization B. Provider work runs between them. | Owner direction OD-X05a / G0 B2 only. Needs adopted BE2-01 lifecycle scope (Rev7) and BE2-08 participant scope (Rev3) plus supplemental approvals. |
| X05b | BE2-08 publishes a read-only finalized-artifact model. **BE2-09 owns** the canonical review head, immutable review history, idempotency receipt and combined DATA-27 projection, keyed to the exact BE2-08 artifact hash and version (OD-X05b, G0 B5). | BE2-09 must not write BE2-08 rows, schemas or migrations; a shared DATA-27 shape change needs a versioned cross-owner CR. Read-after-commit must be proven against the same authoritative store used by finalization; an eventual projection is not authoritative without a version/consistency contract (BE2-08 read-model draft, `FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md`, AR01–AR06). Fields, access, visibility and provenance are not decided. |
| X05c | CR09-02 actual session/access receipt and each-use gateway. | `OPEN`. A playback intent recorded offline does not prove a session start, access grant or playable media. |
| X05d | A current-source resolver/fence **already adopted by its owners (BE2-07 producer, BE2-09 consumer)** that covers both the BE2-09 **review commit** and the **playback intent**. | `BLOCKED` (G0 B6): no adopted resolver/fence has been identified. While blocked, BE2-09 may not record a successful review of a video artifact (BE2-09 scope R05/R07), and X05 cannot pass. |

Rules that follow from OD-X05d and B6:

1. X02 (an invalidation receiver/event delivered to BE2-09) does **not** satisfy X05d. Building X02 does not unblock X05d, and X05d may not be closed by pointing at X02 evidence.
2. Any new receiver, event binding or resolver for BE2-09 needs its own owner decision, card scope and supplemental approval. It is not added through X05 work.
3. The X01 finalization fence (BE2-07 → BE2-08) does not close X05d or X02 (foundation Rev7 §7).
4. If an owner later adopts a resolver/fence, X05d moves only after that adoption is recorded in `FEAT-056-be2-knowledge-script` and `FEAT-051-be2-video-review-playback`, and review-commit plus playback-intent tests pass against it.

### 3.2 X09-08 current state

- State: `NOT_IMPLEMENTED`.
- What exists: the BE2-01 typed router (`backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py:60-67`, wired in `worker.py` `DispatchWorker.handle`) selects a route from `envelope.message.job_type`. It sends the composition-supplied video job type to the registered `VideoDispatchTarget` and keeps `sketch_assistance` on the provider path. Two different rejections exist in `DispatchWorker.handle` (`worker.py:76-82`). `UNSUPPORTED_JOB_TYPE` is returned when the router resolves no route, that is, for an unregistered or malformed job type. `VIDEO_ROUTE_UNAVAILABLE` is returned only when a route resolved as `video` but its target is missing. The router constructor requires the video job type and target together (`typed_dispatch.py:45-46`), so as written that second branch is defensive and is not what an unknown type reaches. This is uncommitted dirty work under the BE2-01 supplemental approval.
- What is missing: `VideoWorkerAdmission.begin` exists only as a Protocol (`backend/src/sketch2life/application/ports/knowledge_video_worker.py:49-50`); no foundation-backed implementation binds the persisted job → run → pin or commits S. The route is chosen from broker message data, not from a persisted job/route mapping (foundation Rev7 §7 requires `job.job_type`, message type and configured route type to match before S).
- Unknown or unregistered job type: no provider is called and the job is not started, but nothing closes it either. The job stays `QUEUED` with an active unstarted attempt; `_recover_unstarted` (`ai_jobs.py:626-655`) republishes it up to `max_publishes` and then `record_dispatch_loss` moves it to a failure state. "No fallback side effect" therefore holds for the provider only. Whether an unsupported type should instead be rejected explicitly at dispatch is a BE2-01 contract decision; it is not chosen here.

## 4. Required lifecycle boundary contract

BE2-01 owns each UoW and its durable receipt/recovery. BE2-08 receives a scoped participant capability and writes only its own rows. Neither FEAT-057 nor BE2-08 may commit a half-pair or claim atomicity across separate commits. Everything in this section is **candidate contract** from the drafts below; none of it is adopted or implemented.

Governing candidate drafts (exact bytes pinned by the Rev5 manifest):

| Draft | Path | SHA256 |
|---|---|---|
| Foundation UoW scope Rev7 | `FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV7_DRAFT_20261021.md` | `BD119A05F72D311BAC299F3E940927DCE80D67DC1CD38EBE87B7D5ACC1B6EAE9` |
| Budget deferral CR Rev2 | `FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_BUDGET_DEFERRAL_CR_REV2_DRAFT_20261021.md` | `55CB59BE00C5A2F40AE8D635FA07F44DDA3FEE000B21C2EBD3414C0EB9D93376` |
| Budget deferral schema CR | `FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_BUDGET_DEFERRAL_SCHEMA_CR_DRAFT_20261021.md` | `92130E78A5C9327B118F5707A6C9D4A5BF826413297332C9B750005F36653EC3` |
| Stale finalization CR Rev2 | `FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_STALE_FINALIZATION_CR_REV2_DRAFT_20261021.md` | `A4E48C46221C995276F88D678DCD62AC2E3C9B321B1CBA972346293AB63C993B` |
| BE2-08 participant scope Rev3 | `FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_REV3_DRAFT_20261021.md` | `66C614FF268E418F27FA4923FB7272A845F7BC7DA8BB225B8CD10032D364F801` |
| BE2-14 deny/defer scope Rev3 | `FEAT-049-be2-ai-policy/plan/CROSS_LANE_BE2_14_SCOPE_REV3_DRAFT_20261021.md` | `02526017042AC56224D2FF63119B0E927EFBC38DE839879632B3831B9ABDABAE` |

Reference drift to fix in the owning records later (not edited here): BE2-14 Rev3 header and the schema CR "contract companion" line still name the superseded `CROSS_LANE_BUDGET_DEFERRAL_CR_DRAFT_20261021.md`, and the BE1 packet names the superseded stale CR draft. This frame uses only the Rev2 CRs above.

### 4.1 Boundary table

| Boundary | Owner and enlisted rows/effects | Required pair and recovery invariant |
|---|---|---|
| A — submit | BE2-01 opens UoW; foundation job/attempt, semantic key, command receipt, outbox and audit, plus BE2-08 queued run and submission receipt. Run `attempt_id` is null. | One intent yields one exact job/run/video lineage. Duplicate or lost acknowledgement resolves from the authoritative receipt; no provider call. **Blocked** until the §4.4 prerequisites are adopted. No approval covers the BE2-01-side change for A, because the BE2-01 supplemental approval is the typed route only. CR08-01 (`OPEN_CANDIDATE`) has no adopted foundation-owned shared UoW/recovery entrypoint. Stop condition (execution manifest): do not implement two commits and describe them as one atomic boundary. |
| S — start | BE2-01 opens UoW; job/run CAS, BE2-08 start CAS and attempt binding. Admission requires all three gates for the actual attempt: current-use eligibility, worker/provider execution authorization, and budget/concurrency reservation proof (§5.1). | `QUEUED → RUNNING` committed as a pair with the exact attempt. An unknown, unavailable, missing or false gate fails closed: no S and no provider. A resource-only denial follows H. Delivery alone is not proof of S. Lost acknowledgement is reconciled from the durable winner; no duplicate start. |
| H — budget hold / resume | BE2-01 locks job and run (both stay `QUEUED`) and writes durable hold metadata, generation and recovery epoch; no lifecycle state change (Rev7 §4 "H", Budget CR Rev2 §3–§5). | Waiting never counts as dispatch loss, never spends recovery allowance, never allocates another attempt, never calls a provider. Endpoints: persisted `RESUMED` after fresh checks (pair stays `QUEUED` until S) or persisted `CLOSED` by a legitimate cancellation/terminal winner. Lost ack replays the persisted winner. |
| B-accepted — successful finalize | BE2-01 opens UoW; job, run, complete source-fence union, BE2-08 exact artifact/ready state, authoritative receipt and outbox/audit. | One winner commits `SUCCEEDED/ACCEPTED` plus exact artifact and `READY_FOR_REVIEW`; duplicate/late attempt cannot replace it. The BE2-01-side change for B-accepted has no approval either, the same CR08-01 stop condition applies, and the BE2-07 same-store fence is a separate gate. |
| B-stale — stale finalize | BE2-01 opens UoW; job `SUCCEEDED/STALE` with result refs, authoritative STALE receipt, BE2-08 terminal stale/no artifact/no ready, and the D3 keep-private intent in one commit (details §4.5). | No artifact/ready. Intent is not physical deletion and never removes an accepted artifact. If refs cannot be mapped, BE1 adoption is missing, or accepted-reference protection is missing, nothing is committed (no partial job/run/intent commit); the operation stays pending/fail-closed. |
| F — failure/retry/timeout/cancel/dispatch loss | BE2-01 opens UoW for job/run and BE2-08 participant rows; reconciler/outbox dispatchers call this same boundary. | Pair CAS and recovery receipt are atomic. Retry respects attempt cap/backoff; timeout/cancel cannot update only one side. Cancel/notice also closes any active hold. |
| F-reject — business reject | Separate BE2-01 reject UoW; job/run, BE2-08 terminal row, authoritative REJECTED receipt and verified owned-ref intent. | A rejection is not a rollback side effect. Replay uses immutable operation identity/reason/ref set. Current source commits rejections inside `accept_completion`; the separate reject boundary is a D1 change, not existing behavior. |
| Guard — intent/audit only | `JOB_CANCELLED`, `JOB_TERMINAL` or `ATTEMPT_SUPERSEDED` precondition. BE2-01 writes durable audit and verified owned-ref quarantine intent; no job/run lifecycle CAS. | Non-authoritative response; does **not** occupy the `(job_id, attempt_id)` completion-receipt slot; preserves the existing winner. A guard STALE never turns an existing run stale. Accepted-reference protection still applies. Source: `_decide_completion` (`ai_jobs.py:966-972`) and the non-authoritative branch of `accept_completion` (`ai_jobs.py:745-768`). |
| I — audit-only incident | `INVALID_STATE`, `INPUT_MISMATCH` (`TEMPORARY_VERDICTS`, `ai_jobs.py:160-161`) or a claim rejected by `_normalise_claim` (`ai_jobs.py:738-740`). | No job/run lifecycle commit and no authoritative completion receipt, but the existing durable audit-only incident **is** persisted (`ai_jobs.py:766-768`); the attempt stays completable. This is not infrastructure recovery from a stage journal. Treating owner "temporary → no commit" as "no lifecycle/authoritative commit, audit kept" is the conservative reading in Rev7 §3; **owner confirmation of that reading (NEW-5) is still pending.** |

Infrastructure failure of a B transaction is separate from I: B rolls back, nothing is committed, and recovery uses a fresh-UoW authoritative lookup (Rev7 §4 commit/recovery matrix). Non-accepted stage recovery needs the durable stage/reject journal, which is still a versioned schema gate.

**Approval status of A and B-accepted.** The foundation side of A and of B-accepted has no approval: BE2-01's only supplemental approval is the typed route. The BE2-08 addendum (`6A195B6F…`) is hash-bound and names two separate atomic boundaries, but it carries the CR08-01 gate and has no recorded execution manifest. Until CR08-01 is adopted and the supplemental approvals exist, an implementation of A or B-accepted that commits job and run in two transactions must not be called a UoW, and no edge that needs either boundary may be reported as passing.

### 4.2 Completion classification and valid persisted axes

Source of both tables: foundation Rev7 §3 and its "Valid persisted axes" table (SHA256 `BD119A05…6EAE9`), aligned with stale CR Rev2 §2–§3 (SHA256 `A4E48C46…3C993B`) and read against `_decide_completion` (`ai_jobs.py:952-1008` at the manifest-pinned bytes). These tables are **adapted**, not reproduced verbatim. The last column marks every row that was added here and every row whose wording or label was adjusted; "Same" means the content matches Rev7. Table 1 follows the order of `_decide_completion`, which differs from Rev7's order. Rev7 and the CR remain the authority: where this text differs from them, Rev7 governs and the difference is a defect to correct here. Candidate contract only.

**Table 1 — `_decide_completion` / `accept_completion` outcome → boundary**

| Source decision (in source order) | Boundary | Job/run action | Receipt/effects | Relation to Rev7 §3 |
|---|---|---|---|---|
| Prior receipt for `(job_id, attempt_id)` | Replay/conflict lookup | Preserve winner | Same fingerprint returns stored receipt; conflicting claim → conflict audit, fail closed. | Reordered (Rev7 lists it last); wording adjusted. |
| Claim rejected by `_normalise_claim` | I | None | Audit-only incident. | Split out of Rev7's combined `INVALID_STATE / INPUT_MISMATCH / failed claim normalization` row; boundary label `I` added. |
| `INVALID_STATE` / `INPUT_MISMATCH` precondition | I | None | Audit-only incident. | Split from the same Rev7 row; boundary label `I` added. |
| `JOB_CANCELLED` / `JOB_TERMINAL` / `ATTEMPT_SUPERSEDED` precondition | Guard intent/audit-only | Preserve winner | Non-authoritative; audit + verified owned-ref intent; no slot. | Boundary label changed (Rev7: `F-reject incident/intent-only`; here `Guard`, kept apart from F-reject); wording adjusted. |
| Eligibility denied for consent/session/source/kill | F-reject | Paired CANCELLED | Authoritative REJECTED receipt + owned-ref intent. | Wording adjusted; same boundary. |
| Eligibility denied only for `BUDGET_EXCEEDED` (provider already ran) | **D4 gate — unclassified** | Pending | Not F-reject, not H, not success. No cancel/quarantine/settle/refund/rerun inferred (D4 ballot). | **ADDED.** Not a row of Rev7 §3. Taken from Rev7's rereview-4 note on the completion-time resource result, the D4 ballot and the `_check()` result. |
| `OutcomeKind.FAILURE` | F | Foundation policy → FAILED_RETRYABLE or FAILED_EXHAUSTED; run mirrors | Authoritative receipt ACCEPTED (acknowledges the failure, not a video). | Label changed (Rev7: `F-failure`; here `F`); wording adjusted. |
| Unsafe output | F-reject | Paired BLOCKED_UNSAFE | REJECTED receipt + owned quarantine intent. | Same. |
| Malformed output (validation fails) | F-reject | Paired FAILED_EXHAUSTED | REJECTED receipt; intent only for verified owned refs. | Wording adjusted. |
| Valid safe success, context superseded | B-stale | Job SUCCEEDED/STALE; run video-terminal STALE, no artifact/ready | Authoritative STALE receipt + same-commit D3 intent. | Wording adjusted. |
| Valid safe success, current context | B-accepted | Job SUCCEEDED/ACCEPTED; run SUCCEEDED with exact artifact/ready | Authoritative ACCEPTED receipt + audit. | Reordered (Rev7 lists it first); wording adjusted. |

**Table 2 — valid persisted combinations**

| Job state | `AiJob.result_disposition` | Completion receipt disposition | Video-run state / output | Relation to Rev7 "Valid persisted axes" |
|---|---|---|---|---|
| SUCCEEDED | ACCEPTED | ACCEPTED | SUCCEEDED, exact artifact, ready. | Same. |
| SUCCEEDED | STALE | STALE | Video terminal STALE, no artifact/no ready, with same-commit D3 intent. | Wording adjusted (`Video terminal STALE` for Rev7's `Video STALE terminal`). |
| FAILED_RETRYABLE / FAILED_EXHAUSTED (failure claim) | None | ACCEPTED | Matching failure state, no accepted artifact. | Wording adjusted. |
| CANCELLED (completion eligibility denial) | None | REJECTED | CANCELLED, no accepted artifact. | Wording adjusted. |
| BLOCKED_UNSAFE | REJECTED | REJECTED | BLOCKED_UNSAFE, no accepted artifact. | Same. |
| FAILED_EXHAUSTED (malformed output) | None | REJECTED | FAILED_EXHAUSTED, no accepted artifact. | Wording adjusted. |
| QUEUED (submitted, held or retry-requeued) | Source-defined | None | QUEUED, `attempt_id` null. | **ADDED.** Not in Rev7's table. Derived from Budget CR Rev2 §3 (a held pair stays `QUEUED`) and the Rev7 §4 A and H rows. It is not a completion outcome. |
| Dispatch loss / admin cancellation / retry / start / timeout | Source-defined lifecycle | None required | Paired outcome of that boundary; no fabricated completion receipt. | Wording adjusted: Rev7 lists `defer` in this row; here `timeout` replaces it, and deferral appears only in the added `QUEUED` row above. |

A non-authoritative guard or I response never replaces these persisted axes. The video stale state, its codec, `TERMINAL_STATES` in `save()`, `_receipt` and the public projection all need the versioned BE2-08 CR (BE2-08 Rev3 §4); current source does not support it.

### 4.3 Lock order (candidate; full lock-path review pending)

Candidate rule, from foundation Rev7 §8 and Budget CR Rev2 §6:

1. Lock **all** required job/run pairs first, in stable ascending job-id order, each job before its run.
2. Then foundation-owned hold/dispatch bookkeeping for those jobs (Budget CR Rev2 §6).
3. Then the **complete** canonical sorted union of source fences, held **once** through commit.
4. Collect every foundation and participant fence need before acquiring fences. If a fence is discovered late, abandon and restart the UoW. Never lock pair 1 → its fences → pair 2, and never append a smaller fence key later.

Recorded exceptions:

- **A (`create_job`)**: holds authorization/eligibility fences before inserting the new job row (`_hold` at `ai_jobs.py:406`, then `insert_job` at `ai_jobs.py:428`). This is an A-only fresh-row exception with reviewed uniqueness/replay; it does not let existing-row writers reverse the order.
- **Invalidators**: an invalidator that commits fence changes first must open a new lifecycle UoW for any later job/run work; it never takes job/run locks while holding fences.
- **Accounting/reservation**: runs in its own transaction outside job/run/fence locks; never nested under a lifecycle lock (Budget CR Rev2 §6, BE2-14 Rev3 §3).
- **Outbox logical lease**: a lease is not a SQL row lock, and no lock or transaction spans broker publish or provider I/O.

Comparison with current source (manifest-pinned bytes; the fence hold is delegated to an owner fence port through `hold_owner_fences`, `repository.py:544-548`, so actual fence locking depends on an owner adapter that is ASSUMED_CONTRACT in the fixture):

| Path | Current lock sequence | Against the candidate rule |
|---|---|---|
| `jobs_for_notice` (`repository.py:881-907`) | Locks every matching job `FOR UPDATE` in job-id order, then rereads each. No run, no fence. | Job order is compatible. Must be revised to lock each paired run after its job and recheck `notice_matches` and run revision after locking, keeping `notice_atomic_max`, one-transaction completion and idempotency (Rev7 §8). Pending. |
| `ack_dispatch` (`repository.py:747-772`) | Non-locking read of the outbox row by lease, then job `FOR UPDATE`, then UPDATE outbox and attempt. | Job before bookkeeping is compatible. Under a hold it must also check the current lease/recovery generation while holding the job (Budget CR Rev2 §5). Pending. |
| `claim_outbox` (`repository.py:694-742`) | Separate transaction; outbox rows `FOR UPDATE SKIP LOCKED`, then UPDATE, with no job lock. | Outbox-before-job exception. SKIP LOCKED means it never waits, but it must exclude held work. Budget CR Rev2 §6 says outbox-claim exceptions need explicit shared-UoW review. **Pending.** |
| `_dispatch_one` (`ai_jobs.py:557-593`) | Non-locking lease check, job `FOR UPDATE`, owner fences, then job CAS and outbox dispose. | Today outbox bookkeeping is written **after** fences; the candidate puts bookkeeping **before** fences. Needs reconciliation in the joint CR review. Pending. |
| `start_attempt`, `retry_job`, `cancel_job` | Job `FOR UPDATE`, owner fences, job CAS (retry also inserts outbox after fences). | No run lock exists yet. Adding run between job and fences follows the rule; retry's outbox insert has the same bookkeeping-order question. Pending. |
| `accept_completion` (`ai_jobs.py:704-787`) | Job `FOR UPDATE`, eligibility + artifact fences in one hold, job CAS, receipt, side effects. | Artifact fences are computed by `_decide_completion` before the hold, in the same transaction. Must become the complete union including source fences, with late-fence restart. Pending. |
| `_recover_unstarted`, `_expire_overdue` | Job `FOR UPDATE`, then outbox insert or job CAS; no fence. | Compatible order; run lock must be added for dispatch loss/timeout (F). Pending. |
| A — creation lease and CR08-01 participant entrypoint | Not in current source. No adopted foundation-owned entrypoint lets BE2-08 rows join `create_job`'s transaction (CR08-01, `OPEN_CANDIDATE`). Rev7 §8 says the creation lease is outside A and is not an enlisted row. | Unreviewed. The review must state where the lease sits relative to job → run → fences, whether any lock or transaction is held while it is held, and how the CR08-01 entrypoint relates to the `create_job` fresh-row exception above. Pending. |

Open items that keep the lock order a **candidate**: multi-pair lock protocol and notice revision; outbox-claim exception; bookkeeping-before-fence reordering in `_dispatch_one`/`retry_job`; the creation-lease placement for A and the CR08-01 shared-UoW entrypoint (no adopted entrypoint exists); source-fence owner/key/invalidator inventory; the BE2-08 participant's own lock paths (BE2-08 Rev3 §6); and a same-store implementation. Deadlock freedom is not claimed until that review passes and durable two-session evidence exists (G8).

### 4.4 Boundary A prerequisites and envelope invariant

A is **blocked**. It cannot be implemented or claimed until these are adopted in the owning records:

1. **Retry-policy mapping.** `JobRetryPolicy` has `policy_id`, parameters and `status` but no version or hash (`backend/src/sketch2life/domain/ai_jobs/model.py:103-112`); the foundation supplies it through dependencies (fixture default). `VideoPin.retry_policy` is an exact ref compared by ref/version/hash (`backend/src/sketch2life/application/knowledge_video_create.py:49-50`). A versioned mapping must be adopted jointly by BE2-01 (`FEAT-044-be2-ai-job-foundation`) and BE2-10 (`FEAT-052-be2-video-failure-disposition`) (Rev7 §2/§7, slice plan Rev8 §4). BE2-10's current plan excludes a global retry-policy replacement (`FEAT-052-be2-video-failure-disposition/plan/PLAN.md:31-33`, scope exclusions), so this needs a new joint CR. None exists yet.
2. **Request fields without counterparts.** `request_id`, `request_revision`, `input_hash`, `target_id`, `purpose_code` and `subject_refs` have no proven VideoPin/run counterpart. Each needs an owner-approved mapping or versioned CR; equality to `video_id`, `pin_digest` or an artifact hash may not be assumed (Rev7 §7).
3. **Session.** Foundation `scope.session_id` must equal `VideoPin.session_id`; a null foundation session fails closed.
4. **Job type.** `job.job_type`, the dispatch message type and the configured route type must match through a versioned typed-route mapping before S; there is no job-type field on VideoRun.
5. **Dual semantic indexes.** Foundation command/semantic identity and the BE2-08 receipt/session-pin index must reconcile to one exact winner in the same UoW.

Envelope invariant: `WorkerDispatchEnvelope` stays unchanged. No field (epoch, pin, run id, policy ref) is added to it. Job → run → pin mapping is read only from persisted foundation and BE2-08 data under the BE2-01 UoW. Any envelope change needs a separately reviewed and approved scope (BE2-01 supplemental approval; Rev7 §1; Rev8 §1).

### 4.5 B-stale ownership, order and BE1 dependency

- Owners: BE2-01 changes the authoritative stale branch of `_decide_completion` through the stale CR Rev2. BE2-08 changes its model state, codec, `TERMINAL_STATES` in `save()`, `_receipt`, persistence and projection through BE2-08 Rev3. The BE1 artifacts owner must adopt descriptor/quarantine semantics. The BE1 request is `evidence/notes/CROSS_LANE_BE1_ARTIFACTS_ADOPTION_PACKET_DRAFT_20261021.md`, status `DRAFT / NOT_SENT`; no BE1 response or adoption exists.
- Order: preconditions → eligibility → failure/unsafe → **output validation** → context comparison. Malformed output is F-reject before any stale classification; only validated output can become B-stale (stale CR Rev2, rereview-4 notes).
- Descriptors: the adopted artifacts contract must distinguish FOUND, authoritative ABSENT and UNAVAILABLE. Today `describe()` returns `None` for both of the last two. UNAVAILABLE stays pending/recoverable; ABSENT for a referenced output is unmappable and fails closed. A no-ref intent needs explicit BE1 adoption. Without a mappable, owner-proven descriptor for the exact organization/job/attempt, B-stale commits nothing.
- Effects: intent means keep private / clean the private stage only. It never deletes or hides an accepted artifact; accepted output wins in both race orders. Physical cleanup and storage-side fencing are BE1 responsibilities, and intent durability is not proof of deletion.
- Identity: deterministic operation/event identity and the fixed `STALE_CONTEXT` reason are review candidates (stale CR Rev2 §4, rereview-4), not BE1-approved capabilities.

## 5. Budget and policy invariants

Detailed rules live in Budget CR Rev2 §3 (phase/state transitions), §4 (end of deferral), §5 (delivery, timers, counters, recovery) and §6 (transactions/accounting). This section summarizes them; it does not replace them.

1. C1-A holds job and run in `QUEUED` while a durable BE2-01 hold is active; no new `JobState` or video budget state. A due, otherwise authorized retry is requeued once under its normal retry policy, atomically with the hold, to one new attempt. `VideoRun.attempt_id` remains null until S.
2. Paths the hold must cover (Budget CR Rev2 §5): `claim_outbox` excludes held work and begin-defer parks or invalidates claimed leases; `_dispatch_one` rechecks the hold after lease and job/run locks; `ack_dispatch` cannot raise effective dispatch counts, refresh a start timer or undo a hold; `_recover_unstarted` and `queued_dispatched_not_started` exclude held work in selection and in the locked recheck, so hold time never leads to `record_dispatch_loss`; `run_due_retries`/`retry_job` cannot allocate another attempt for held work; cancel and `apply_cancellation_notice` close the hold and invalidate resume and delivery generations; resume installs one current recovery epoch/dispatch intent (re-dispatch after resume) and replays its persisted winner; `expire_overdue_attempts` applies only after a real S. Query filters are optimizations; every mutator rechecks the hold under the paired lock.
3. `BUDGET_EXCEEDED` in `_dispatch_one`, `start_attempt` and `retry_job` defers; consent and kill-switch denial keep their cancellation behavior. BE2-14 can deny/defer but cannot choose a budget, issue execution permission, or mutate foundation/video lifecycle.
4. No reserve or settle call is made while job/run/fence locks are held. Unknown execution or reservation outcome is not terminal evidence and cannot release, refund or authorize another provider run.
5. Budget unit/limit, max hold duration and what it counts, deadline action, reservation expiry/renewal, and a phase mapping for S are explicit pending contract/owner inputs. No number, TTL, scheduler or automatic cancel/fail/refund is invented.
6. D4 must decide completion-time `BUDGET_EXCEEDED` after provider work. Until then `_decide_completion` cannot classify it as pre-execution hold, consent/kill rejection, success, or cleanup.

### 5.1 Three separate authorities

| Authority | Owner | Meaning | Missing / unknown / unavailable |
|---|---|---|---|
| Current-use eligibility | BE2-14 policy contract, consumed by BE2-01 and each consumer | Consent, session, source, audience, kill switch: may this work or result be used now? | Fail closed. A real denial cancels through F/F-reject. |
| Worker/provider execution authorization | Separately adopted grant (BE2-14 / owner); none exists for BE2-08 today | May this exact attempt call a provider? | Fail closed: no S, no provider. Not inferred from eligibility or from a missing denial. |
| Budget/concurrency reservation and accounting | BE2-14 accounting (own transaction) with the joint BE2-01/14 CR | Is there a reservation for this exact persisted attempt? | Resource-only denial → H (hold). Unknown proof keeps the hold pending; never a grant. |

A typed split between resource denial and current-use denial must come from the versioned BE2-14 contract (Budget CR Rev2 §2: the mapping from BE2-14 vocabulary to BE2-01 `BUDGET_EXCEEDED`/defer must be jointly adopted). Today one `_check()` result (`ai_jobs.py:1239-1242`) carries both.

### 5.2 Eligibility call sites

All current `_check()` / eligibility call sites in `backend/src/sketch2life/application/services/ai_jobs.py` (manifest-pinned bytes):

| Call site | Current behavior on `BUDGET_EXCEEDED` | Target | Status |
|---|---|---|---|
| `create_job` (A), lines 389-393 | Raises `BUDGET_EXCEEDED` (429, retryable); no job is created. | Not covered by D3, Rev7 or the Budget CR. Keep current reject, or create a held pair? | **Owner decision gate (BE2-01/BE2-14).** Not chosen here. |
| `_dispatch_one`, lines 566-583 | Cancels the job and disposes the outbox row. | H: hold, park delivery, no cancel, no publish (D3 C1-A). | Candidate in Budget CR Rev2; not adopted or implemented. |
| `start_attempt` (S), lines 662-683 | Cancels the job. | H: hold with no S and no provider; S also needs execution authorization and reservation (§5.1). | Candidate; S phase mapping pending. |
| `accept_completion` → `_decide_completion`, lines 727, 974-979 | Cancels and quarantines output (generic ineligible branch). | Unclassified until D4. | **D4 owner decision pending.** |
| `retry_job`, lines 901-913 | Cancels the job. | Requeue once to a held `QUEUED` pair (D3 C1-A). | Candidate; not adopted or implemented. |
| `get_job_status` (read), lines 935-940 | `expose_results` requires `_check(job).eligible`, so a `SUCCEEDED/ACCEPTED` result is hidden while budget is exhausted. | Candidate invariant, **not adopted**: budget exhaustion would not hide an ACCEPTED result and would not be presented as consent/access revocation; only current-use denial would hide it. | **Owner decision gate (BE2-01 read contract with BE2-14 typed split).** Not covered by any current CR. Not chosen here. |

**Candidate invariant, pending owner decision at three places: A-time, the `get_job_status` read path and D4.** Budget exhaustion would be neither a consent/access revocation nor a reason to hide an ACCEPTED result. This is a candidate only. It is not an owner decision, it is not an exit criterion (§7), and it is not chosen at any of the three call sites. Until those three gates are decided and a typed resource/current-use split is adopted, no evidence may claim that A, the read path or completion handling is budget-correct, and an implementation must not pick either behavior on its own.

## 6. Work sequence and review gates

| Step | Work and owning records | Exit gate |
|---|---|---|
| G0 — Preserve and pin | Take a **read-only snapshot** of the dirty candidate (154 paths at Rev5 start, 152 at Rev4 start, 150 at Rev3 start): per path, status, size and SHA256 in a manifest, grouped by owner/source/test/docs/evidence/local; keep ignored local evidence separate. No stash, commit, reset, clean, checkout or branch change belongs to this scope; any of them needs its own explicit instruction. Pin branch/tree and current card refs. Do not branch from `1649b729` while treating the dirty worktree as published. Record that the BE2-01 typed-route files (`backend/src/sketch2life/infrastructure/ai_jobs/worker.py` modified, `typed_dispatch.py` and `backend/tests/unit/test_ai_job_video_dispatch.py` added) were changed **here** under the `FEAT-044-be2-ai-job-foundation` supplemental approval (§1.3). They stay as pre-existing changes; FEAT-057 does not take ownership of, commit or move them. Where they are committed, and by whom, is a BE2-01 owner decision. **The card documents are a second group of pre-existing changes:** the modified and untracked records of `FEAT-044`, `FEAT-049`, `FEAT-050`, `FEAT-051` and `FEAT-056` (19 modified and 30 untracked paths at Rev3 start: CONTEXT, DECISIONS, approvals, evidence, status, scope and CR drafts, implementation-approval drafts) are not FEAT-057's. This plan neither edits nor commits them. Their disposition is decided by each card owner and is recorded here as an open G0 item, not resolved. The FEAT-057-owned composition files (`backend/src/sketch2life/infrastructure/cross_lane/`, `backend/tests/integration/be2_cross_lane/`), the FEAT-057 records and the FEAT-057 entries in the two `docs/context` ledgers are a third group, committed only on explicit instruction. | Exact, reproducible read-only snapshot manifest; every dirty path is assigned to one of the groups with a named owner who decides its disposition; nothing is stashed, committed, reset or discarded in this scope. |
| G1 — Resolve contracts first | Review the Rev7/Rev3 scopes and Rev2 CRs; fix their stale cross-references. Decide D4. Decide A-time and `get_job_status` budget behavior (§5.2). Obtain budget unit/limits/max duration/deadline action, S reservation phase/expiry rules and the BE2-14 typed resource/current-use split. Adopt the BE2-01/BE2-10 versioned retry-policy mapping and the request/session/job-type mapping (§4.4). Obtain BE1 descriptor tri-state, quarantine and accepted-reference adoption. Adopt the BE2-07 same-store fence (X01). **Adopt, or keep BLOCKED, the X05d current-source resolver/fence (BE2-07/BE2-09) for review commit and playback intent.** Adopt the BE2-08 read model and BE2-09 X05b projection, the X05c playback/session contract, and separately X02 invalidation, X04 publication consumers, X06 failure bridge, X07 preset/session dispatch, X08 phase policy and X09 handler/persisted mapping. Complete the lock-path review (§4.3), including the creation-lease placement for A and the CR08-01 shared-UoW entrypoint. Decide CR08-01, or keep A and the foundation side of B-accepted blocked. | Each edge has a named public contract, owner, exact version/fields, recovery semantics, tests and matching supplemental card approval. A missing contract keeps that edge blocked; a missing §4.4 prerequisite keeps A and every edge that needs A blocked. |
| G2 — BE2-01 lifecycle core | In `FEAT-044-be2-ai-job-foundation`, independently review the latest UoW, budget, schema and stale CRs and obtain separate supplemental approvals for A, S, F, H, B-accepted, B-stale and F-reject and for each new schema. **Entry blockers, per boundary** (an item missing for one boundary blocks only that boundary; the "Missing condition" column of §6.1 is the authoritative list and this passage mirrors it). **A:** BE2-01 supplemental approval; CR08-01; every §4.4 prerequisite; the A-time budget decision; the lock-path review including the creation lease; the AP-08 execution manifest. **S:** BE2-01 S supplemental approval; a worker/provider execution authorization (none exists for BE2-08); an S phase mapping with reservation expiry/renewal terms; the BE2-14 typed resource/current-use split; CR08-01; the AP-08 and AP-14 execution manifests; the lock-path review. **H:** BE2-01 H supplemental approval and a separate schema/new-migration approval (the migration path is unassigned); adoption of Budget CR Rev2 and the schema CR; the owner's budget unit/limit, max hold duration and deadline action; reservation expiry/renewal; the BE2-14 typed split; the AP-14 execution manifest; a lock-path review that covers the claim, ack, recovery and retry paths. **B-accepted:** BE2-01 B-accepted supplemental approval; CR08-01; the same-store durable source fence; D4; the lock-path review; the AP-07 and AP-08 execution manifests. **B-stale:** BE1 adoption of the descriptor tri-state, quarantine and accepted-reference protection (packet `NOT_SENT`); BE2-01 and BE2-08 supplemental approvals; the versioned BE2-08 stale-state/codec/receipt CR; the identity/journal CR; D4; CR08-01; the AP-08 execution manifest. **F:** BE2-01 F supplemental approval; the lock-path review including the multi-pair and notice revision; the BE2-01/BE2-10 retry-policy mapping; the AP-08 execution manifest; H coverage so that cancel closes a hold. **F-reject:** a separate reject-UoW supplemental approval; the stage/reject journal schema scope and approval; BE1-adopted owned-ref descriptors; D4 (a `BUDGET_EXCEEDED`-only denial stays outside F-reject until decided); CR08-01; the AP-08 execution manifest. D4 gates the completion decision as a whole (§4.2 Table 1), which is why it is listed for B-accepted, B-stale and F-reject. Then implement only the approved boundaries. New schema uses a separate CR/migration; never rewrite published migration history. | **Tier O (§6.2):** unit and domain tests on process-local fakes show the paired-CAS rules, replay and lost-ack shapes, scripted stale/finalize orderings, retry/hold accounting, guard and I behavior, and incident handling against the contract. They do not show durability, SQL isolation, lock order or the real race winner; that is tier D at G8. A stays unimplemented while any §4.4 item or CR08-01 is missing. |
| G3 — Source and publication producers | In `FEAT-056-be2-knowledge-script` and `FEAT-048-be2-content-publication`, implement/adopt the exact current-source fence (X01) and published-content adapter (X03); publish identity/hash/audience/recall semantics. Preserve public contracts and prove both race orders. The X05d resolver/fence for BE2-09 is a separate owner adoption, not a by-product of this step. | **Tier O:** producer-created pins are consumed by BE2-08 and both fence/finalize orders pass on process-local fakes. **Tier D (G8, separate database approval):** the same-store durable fence spans finalization. Without tier D, X01 remains `PARTIAL`. |
| G4 — BE2-08 participant and worker | In `FEAT-050-be2-knowledge-video`, adopt the supplemental lifecycle schema/model/codec/receipt/journal/projection scope. Bind worker admission (`VideoWorkerAdmission.begin`) to persisted job/run/pin under the BE2-01 UoW, commit S, execute outside the UoW, then route typed completion per §4.2. Implement the read-only artifact model for X05b only after field/access/provenance decisions. | **Tier O:** real service composition on fakes shows A/S/H/B/F pair-behavior shapes, stage recovery, idempotency, stale output and exact artifact lineage. Read-after-commit on the finalization store and race winners are tier D (G8); fakes do not show them. |
| G5 — Review and failure consumers | In `FEAT-051-be2-video-review-playback`, integrate X05b (BE2-09 review head/DATA-27 projection over the adopted BE2-08 read model) and X04. In `FEAT-052-be2-video-failure-disposition`, integrate X06. X02 proceeds only under its own approved scope. While X05d is blocked, BE2-09 records no successful video review and X05 stays incomplete. X05c stays gated until CR09-02 is resolved. | Exact target/version is reviewed under an adopted X05d gate; replay/lost-ack/late-result races have one winner (scripted on fakes at tier O; real concurrency is tier D); stale/recalled content cannot be reviewed or played. Without X05d this exit is not met. |
| G6 — Other graph consumers and policy | In `FEAT-053-be2-activity-execution` and `FEAT-054-be2-preset-automation`, integrate X04 to BE2-11 and X07 to BE2-13→BE2-01. In `FEAT-049-be2-ai-policy`, implement only separately approved BE2-14 policy phases used by BE2-03 (`FEAT-049-be2-assistance-orchestration`), BE2-04 (`FEAT-050-be2-sketch-generation`), BE2-08 and BE2-13. Complete X09 handler routes for BE2-02 (`FEAT-048-be2-vision-correction`), BE2-03, BE2-04, BE2-08 and BE2-13. | Explicit intent, correct policy phase, disable-generation race and dedup are asserted before side effects; no test-only scheduler/database shortcut. |
| G7 — FEAT-057 composition matrix | Compose real application services with deterministic external adapters. Test each X01–X09 producer-to-consumer edge separately (X05 per sub-edge), then the linked generation→review/playback and failure-disposition paths. Include mismatch, revoke/recall, duplicate, lost ACK, late result, retry, timeout, stale, guard, policy deny/defer/hold and accepted-vs-cleanup races. Preserve BE2-03→06 chain regression. | One pinned snapshot produces JUnit/log/hash receipts per suite and an edge matrix with `PASS/FAIL/BLOCKED/NOT_RUN`; no edge or sub-edge is omitted. The matrix records tier O and tier D in separate columns, and a tier-O result never fills a tier-D cell, which stays `NOT_RUN` until G8. |
| G8 — Durable conformance and final review | After separate approval, run the database/store conformance needed to prove durable source-fence winner order, lock order/deadlock behavior, transaction rollback/recovery and schema graph. This is the only gate that may support durable, SQL, lock-order, deadlock or race-winner claims, and it needs its own database approval, because the FEAT-057 approval excludes shared SQL/database provisioning. Obtain independent review and each changed card owner's review. Re-pin final source and run affected suites/validators. | Every required edge passes on the same reviewed tree; tier-D claims have actual durable-store evidence, not just process-local fakes. |
| G9 — BE1 handoff | Split owner commits by card; integrate only reviewed SHAs into the shared BE2 branch. Publish a clean PR/snapshot only after security checks and explicit Git-publication approval. Provide BE1 exact branch/commit, contracts, tests, limitations and adopted artifact seam. | `READY_FOR_BE1_HANDOFF` means BE2 code/contracts are reviewable and all required BE2 edges are evidenced. It does not mean BE1 integration, production, Lightning, or card acceptance is complete. |

Dependencies are intentional: G1 precedes every implementation step; G2 precedes G4; X01/X03 producer contracts precede video submission; X05 depends on B-accepted, the BE2-08 read model, the BE2-09 projection **and** an adopted X05d gate; X02/X04/X06 depend on those owner interfaces; X07/X08/X09 require policy and dispatch contracts. Work may be prepared in parallel only on isolated owner branches after exact scopes are approved; merge reviewed SHAs into the shared integration branch sequentially in dependency order.

### 6.1 Boundary scope table (for approval review; not itself an approval)

This is the table a reviewer or the owner can use to decide which boundary, if any, to approve next. Path convention: `src:` means `backend/src/sketch2life/`, `tests:` means `backend/tests/`. Every path below is a **candidate**; none is a frozen execution subset. Provenance differs by row and is stated in the provenance table after the approval reference. There are three classes: *named* (a draft lists the file for that change), *from a list, assignment inferred* (a draft lists the file for a wider scope and attaching it to this boundary is this plan's reading) and *inferred* (no draft lists the file for this change; the plan derived it from where the cited functions live). The boundary table marks the last two. An inferred or assignment-inferred path is a hypothesis, not a statement of any draft, and the owner must confirm or replace it in the execution manifest. Foundation Rev7 lists no file paths. Nothing here approves code: the approvals that exist are bound to their own hashes and are listed first.

**Approval reference** (file SHA256 as pinned in the Rev5 manifest; every file is a modified, uncommitted worktree file):

| ID | Approval record | Approved addendum or plan (SHA256) | What it covers | Execution file subset recorded? |
|---|---|---|---|---|
| AP-01 | `FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md`, supplemental cross-lane dispatch approval; file `9E8AA39CBBAC3C1CEECAA489194344E8C211200F18839BA2B3B10FBE9A47611D` | `plan/CROSS_LANE_BE2_01_SCOPE_DRAFT_20261021.md`, `AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD` | Typed route for the adopted BE2-08 job type; unknown types fail closed; envelope, schema and provider path unchanged. | Yes: `src:infrastructure/ai_jobs/worker.py` (modify), `src:infrastructure/ai_jobs/typed_dispatch.py` (add), `tests:unit/test_ai_job_video_dispatch.py` (add); `tests:unit/test_ai_job_b5_capability.py` is a read-only regression. |
| AP-07 | `FEAT-056-be2-knowledge-script/approvals/TASK_APPROVAL.md`; file `410295D02552A02D98358C122AFD19B3CE4B5A9A006B875EA5F8970A5B7B37C9` | `plan/CROSS_LANE_BE2_07_SCOPE_DRAFT_20261021.md`, `CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24` | Producer-owned exact source identity/currentness and tests. The fence through BE2-08 finalization is an explicit adoption and proof gate; the process-local coordinator is not accepted as a durable fence. | No. |
| AP-08 | `FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md`; file `8B5F6E924FB1B9F05CEFF6310592EF159B1F374443834C9B35A0685A56002383` | `plan/CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md`, `6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0` | Two separate atomic boundaries for submission and finalization with external generation between them; replay, lost-ack, late-result; CR08-01 and owner-boundary details remain explicit gates; a migration or unlisted/shared-contract path needs a revised scope. | No. |
| AP-09 | `FEAT-051-be2-video-review-playback/approvals/TASK_APPROVAL.md`; file `90A3066646BA8F66F0C550BDE6CCB81A38A670A38309CB362FD82741DCE23C24` | `plan/CROSS_LANE_BE2_09_SCOPE_DRAFT_20261021.md`, `121699BE6A3134C65EF16917941FA75F00401EA18462BA929C2E897BCAB46285` | CR09-01 review-owned canonical head and DATA-27 projection bound to the exact committed BE2-08 artifact. X05d stays `BLOCKED`, X05c/CR09-02 `OPEN`; no X02, session/access gateway or playback. | No. |
| AP-14 | `FEAT-049-be2-ai-policy/approvals/TASK_APPROVAL.md`; file `5CF16072984E7A3C17D6E6046B7BB2E9795074EC061CC006FF16126D4A7725A4` | `plan/CROSS_LANE_BE2_14_SCOPE_DRAFT_20261021.md`, `417A740BA60E624BE2AA78D861E8DAEF80094AAF9992C3E65E782EB7EA78C9D8` | BE2-08 request/phase mapping, current-use fences, a separate worker/provider execution authorization, budget reservation and settlement contracts, on existing schemas only; no BE2-08 call-site changes. Its PostgreSQL provisioning approval is separate and unchanged. | No. |
| AP-57 | `FEAT-057-be2-01-14-offline-integration/approvals/TASK_APPROVAL.md`; file `66BFD26AD0CF8646FBC0D8097C2B957939A43F74E42739E50BF83CABD9936557` | `plan/CROSS_LANE_INTEGRATION_PLAN_REV2_20261020.md`, `2015173C1FDADEBBE5D01ADD8844160F24F10E2B495250F67A927529B44C570B` | FEAT-057-owned composition and adapters under `src:infrastructure/cross_lane/`, tests under `tests:integration/be2_cross_lane/`, and FEAT-057 records. Excludes card-owned source, contracts and migrations, shared SQL/database provisioning and route mounting; stops where a card contract is missing. | Paths are named in the approval. |

BE2-02, BE2-10, BE2-11, BE2-12 and BE2-13 have no row because this plan makes no approval claim about them (§1.5).

**Provenance of the candidate paths, by row:**

| Row | BE2-01 file set | Other-card file sets |
|---|---|---|
| A | inferred: Budget CR Rev2 does not cover `create_job` (§5.2) | BE2-08 files from the BE2-08 Rev3 §8 candidate list; assignment inferred |
| S | from Budget CR Rev2 §7, which lists them for the deferral scope (it covers `start_attempt`); assignment to S inferred | BE2-08 files from BE2-08 Rev3 §8, assignment inferred; BE2-14 primary paths named by BE2-14 Rev3 §5 |
| H | named: Budget CR Rev2 §7 and budget schema CR §6 | BE2-14 primary paths named by BE2-14 Rev3 §5 |
| B-accepted | inferred: neither Budget CR Rev2 nor stale CR Rev2 lists a changed-file set for the successful-completion path | BE2-08 files from BE2-08 Rev3 §8, assignment inferred; BE2-07 files named by the BE2-07 addendum |
| B-stale | `ai_jobs.py` named by stale CR Rev2 §7; `ports/ai_jobs.py` and `completion.py` appear there only as governing contracts, so listing them as possible changes is this plan's reading | BE2-08 file set named by stale CR Rev2 §7, except the two port filenames, which come from BE2-08 Rev3 §8 |
| F | from Budget CR Rev2 §5 and §7, which cover these hold paths (`reconciler.py` and `outbox_dispatcher.py` "only if wiring changes" is that CR's wording); assignment to F inferred | BE2-08 files from BE2-08 Rev3 §8, assignment inferred |
| F-reject | inferred: no draft lists a changed-file set for the reject branches | BE2-08 files from BE2-08 Rev3 §8, assignment inferred |
| Guard, I | existing source; no change proposed | none |
| Typed route | named: BE2-01 addendum | none |

**Boundary table:**

| Boundary | Owner and card | Candidate paths to change (not frozen; `inferred` marks this plan's own reading; see the provenance table above) | Existing approval | Missing condition or supplemental approval | Allowed now | Recovery and conformance gate |
|---|---|---|---|---|---|---|
| A — submit | BE2-01 `FEAT-044-be2-ai-job-foundation` (UoW, `create_job`); BE2-08 `FEAT-050-be2-knowledge-video` (queued run and submission receipt); BE2-10 `FEAT-052-be2-video-failure-disposition` (retry-policy mapping co-owner) | BE2-01 (inferred): `src:application/services/ai_jobs.py`, `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py`, `src:infrastructure/ai_jobs/fakes.py`. BE2-08 (assignment inferred): `src:application/knowledge_video_create.py`, `src:application/ports/knowledge_video.py`, `src:infrastructure/knowledge_video/sql.py`. | AP-01 does **not** cover A. AP-08 is hash-bound for the two boundaries and has no execution manifest. | BE2-01 supplemental approval for A (none exists); CR08-01 adoption (foundation-owned shared UoW/recovery entrypoint); every §4.4 prerequisite; the A-time budget decision; the lock-path review incl. creation lease; an AP-08 execution manifest. | None on source or tests. | Tier O: replay, duplicate and lost-ack on fakes. Tier D (G8): actual PostgreSQL transaction and restart evidence required by CR08-01. |
| S — start | BE2-01 (UoW, `start_attempt`); BE2-08 (start CAS, attempt binding); BE2-14 `FEAT-049-be2-ai-policy` (eligibility, execution authorization, reservation contract) | BE2-01 (from Budget CR Rev2 §7; assignment inferred): `src:application/services/ai_jobs.py`, `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py`, `src:infrastructure/ai_jobs/fakes.py`. BE2-08 (assignment inferred): `src:application/knowledge_video_worker.py`, `src:application/ports/knowledge_video_worker.py` (`VideoWorkerAdmission.begin`), `src:domain/knowledge_video/model.py`, `src:infrastructure/knowledge_video/sql.py`, `src:infrastructure/knowledge_video/codec.py`. BE2-14 (primary): `src:contracts/schemas/ai_policy_use.py`, `src:application/ports/ai_policy_use.py`, `src:application/ai_policy_use.py`. | AP-08 and AP-14 are hash-bound, without execution manifests. AP-01 does not cover S. | BE2-01 S supplemental approval (D1 requires it); a worker/provider execution authorization (none exists); S phase mapping and reservation expiry/renewal; BE2-14 typed split; CR08-01; AP-08 and AP-14 execution manifests; lock-path review. | None. | Tier O: pair CAS, lost-ack replay, no S and no provider when any gate is unknown. Tier D: committed S pair and duplicate-start winner on the real store, two-session lock order. |
| B-accepted — successful finalize | BE2-01 (UoW, completion decision, source-fence union); BE2-08 (exact artifact and ready state); BE2-07 `FEAT-056-be2-knowledge-script` (X01 currentness fence) | BE2-01 (inferred): `src:application/services/ai_jobs.py` (`accept_completion`, `_decide_completion`), `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py`, `src:infrastructure/ai_jobs/fakes.py`. BE2-08 (assignment inferred): `src:application/knowledge_video_worker.py`, `src:application/ports/knowledge_video_worker.py`, `src:domain/knowledge_video/model.py`, `src:infrastructure/knowledge_video/sql.py`. BE2-07: `src:application/ports/knowledge_bundle.py`, `src:application/services/knowledge_bundle.py`, `src:infrastructure/knowledge_bundle/coordination.py`, `src:infrastructure/knowledge_bundle/fakes.py`, `tests:unit/test_knowledge_bundle_service.py`, `tests:unit/test_knowledge_bundle_races.py`. | AP-07 and AP-08 are hash-bound, without execution manifests. AP-01 does **not** cover B-accepted. | BE2-01 B-accepted supplemental approval (none exists); CR08-01; the same-store durable source fence (execution manifest stop condition: re-read-only evidence stays X01 `PARTIAL`); D4; lock-path review; AP-07 and AP-08 execution manifests. | None. | Tier O: both invalidation/finalize orders scripted on fakes. Tier D: the durable fence held through the finalization commit and the real race winner. |
| B-stale — stale finalize | BE2-01 (stale branch, same-commit intent); BE2-08 (stale state, codec, receipt, projection); BE1 artifacts owner (descriptor and quarantine adoption, outside the BE2 cards) | BE2-01: `src:application/services/ai_jobs.py` (stale branch of `_decide_completion`; named by stale CR Rev2 §7); `src:application/ports/ai_jobs.py` and `src:domain/ai_jobs/completion.py` (the stale CR calls them governing contracts; listing them as possible changes is this plan's reading). BE2-08 (file set named by stale CR Rev2 §7; the two port filenames from BE2-08 Rev3 §8): `src:domain/knowledge_video/model.py`, `src:infrastructure/knowledge_video/codec.py`, `src:infrastructure/knowledge_video/sql.py`, `src:application/knowledge_video_worker.py`, `src:application/knowledge_video_create.py`, `src:application/ports/knowledge_video.py`, `src:application/ports/knowledge_video_worker.py`, `src:contracts/schemas/knowledge_video.py` (versioned projection only). BE1: none in this scope. | AP-08 is hash-bound; the state, codec and receipt change needs a versioned BE2-08 CR. None for BE2-01. | BE1 adoption of the descriptor tri-state, quarantine and accepted-reference protection (packet `NOT_SENT`); BE2-01 and BE2-08 supplemental approvals; the versioned BE2-08 stale-state CR; identity/journal CR; D4; CR08-01; AP-08 execution manifest. | None. | Tier O: stale versus accepted in both orders; nothing is committed when a descriptor is unmappable. Tier D: same-commit intent durability and race winner. Physical cleanup is BE1's and out of scope. |
| F — failure, retry, timeout, cancel, dispatch loss | BE2-01 (UoW, reconciler, outbox); BE2-08 participant; BE2-10 (retry-policy mapping co-owner) | BE2-01 (from Budget CR Rev2 §5 and §7; assignment inferred): `src:application/services/ai_jobs.py` (`retry_job`, `cancel_job`, `_recover_unstarted`, `_expire_overdue`), `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py` (`jobs_for_notice`, `ack_dispatch`, `claim_outbox`), `src:infrastructure/ai_jobs/fakes.py`; `src:infrastructure/ai_jobs/reconciler.py` and `src:infrastructure/ai_jobs/outbox_dispatcher.py` only if the adopted wiring changes. BE2-08 (assignment inferred): `src:application/knowledge_video_worker.py`, `src:domain/knowledge_video/model.py`, `src:infrastructure/knowledge_video/sql.py`. | AP-08 is hash-bound, without an execution manifest. AP-01 does not cover F. | BE2-01 F supplemental approval (none exists); the lock-path review, including the multi-pair and notice revision; the BE2-01/BE2-10 retry-policy mapping; AP-08 execution manifest; H coverage for cancel closing a hold. | None. | Tier O: attempt cap and backoff, pair CAS, recovery receipt on fakes. Tier D: timeout/cancel pair atomicity, restart recovery and notice atomicity on the real store. |
| F-reject — business reject | BE2-01 (separate reject UoW); BE2-08 (terminal row); BE1 artifacts owner (owned-ref intent adoption) | BE2-01 (inferred): `src:application/services/ai_jobs.py` (reject branches of `accept_completion`/`_decide_completion`), `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py`, `src:infrastructure/ai_jobs/fakes.py`. BE2-08 (assignment inferred): `src:domain/knowledge_video/model.py`, `src:infrastructure/knowledge_video/sql.py`, `src:application/knowledge_video_worker.py`. A stage/reject journal path is unassigned. | AP-08 is hash-bound. None for BE2-01. | A separate reject-UoW supplemental approval; the stage/reject journal schema scope and approval; BE1-adopted owned-ref descriptors; D4 (a `BUDGET_EXCEEDED`-only denial is not F-reject); CR08-01; AP-08 execution manifest. | None. | Tier O: replay of the immutable operation identity, reason and ref set. Tier D: the separate commit, its rollback behavior and recovery on the real store. |
| H — budget hold / resume | BE2-01 (hold metadata and the claim, ack, recovery, retry and cancel paths); BE2-14 (deny/defer contract) | BE2-01: `src:application/services/ai_jobs.py`, `src:application/ports/ai_jobs.py`, `src:infrastructure/ai_jobs/sql/repository.py`, `src:infrastructure/ai_jobs/sql/tables.py`, `src:infrastructure/ai_jobs/fakes.py`; `src:domain/ai_jobs/model.py` only for a reviewed auxiliary protocol, never a new `JobState`; `src:infrastructure/ai_jobs/reconciler.py` and `src:infrastructure/ai_jobs/outbox_dispatcher.py` only if wiring changes; the new migration path is **unassigned**. BE2-14 (primary): `src:contracts/schemas/ai_policy_use.py`, `src:application/ports/ai_policy_use.py`, `src:application/ai_policy_use.py`. Tests: `tests:unit/test_ai_job_application.py`, `tests:unit/test_ai_job_b4_dispatch.py`, `tests:unit/test_ai_job_lifecycle.py`, `tests:integration/ai_jobs/test_migrations.py`. | AP-14 covers policy-use mapping on existing schemas; a schema change needs a new scope and approval. AP-01 does not cover H. | BE2-01 H supplemental approval and a separate schema/new-migration approval; adoption of Budget CR Rev2 and the schema CR; the owner's unit/limit, max hold duration and deadline action; reservation expiry/renewal; BE2-14 typed split; AP-14 execution manifest; lock-path review. | None. | Tier O: the BD01–BD07 hold-path cases of Budget CR Rev2 §8 on fakes. Tier D: schema and migration graph, one active hold, lost-ack, restart and race orders on the real store. |
| Guard — intent/audit only | BE2-01; BE1 artifacts owner for the owned-ref intent | Existing behavior in `src:application/services/ai_jobs.py` (`_decide_completion`, non-authoritative branch of `accept_completion`). No change is proposed beyond the classification. | None needed for existing behavior; none for a change. | Accepted-reference protection (BE1) before any change that adds intent behavior. | None. | Tier O: the existing winner is preserved and no receipt slot is occupied. Tier D: intent durability. |
| I — audit-only incident | BE2-01 | None proposed. Existing behavior: `_normalise_claim`, `TEMPORARY_VERDICTS` and the audit-only incident path in `src:application/services/ai_jobs.py`. A change would touch only that file, and only after the owner decides. | None needed for existing behavior; none for a change. | NEW-5: owner confirmation of the conservative reading (no lifecycle or authoritative commit, audit kept). | None. A FEAT-057-owned characterization test through the public service API is permitted in principle by AP-57; none is written in this scope. | Tier O: attempt stays completable and the incident is audited. Tier D: incident durability. |
| Reference: typed route (X09-08 route level) | BE2-01 | `src:infrastructure/ai_jobs/worker.py` (modify), `src:infrastructure/ai_jobs/typed_dispatch.py` (add), `tests:unit/test_ai_job_video_dispatch.py` (add). | AP-01: exact three paths. | Nothing for the route itself. X09-08 stays `NOT_IMPLEMENTED` until the persisted job-to-run-to-pin mapping and committed S exist. | Only those three paths, only to correct a defect in the approved routing behavior. The work already exists, uncommitted. | Route-level unit evidence only. It is not S and not an admission proof. |
| Composition (FEAT-057) | FEAT-057 | `src:infrastructure/cross_lane/`, `tests:integration/be2_cross_lane/`, FEAT-057 records. | AP-57. | The owning card's adopted public contract for each edge. A missing contract keeps the edge `NOT_IMPLEMENTED`. | Composition, adapters and tests inside those paths, only against adopted contracts. It may not edit a card file, simulate a missing contract as passing, or take ownership of the pre-existing changes (G0). | Tier O at G7; tier D at G8. |

An approval reference in this table is not a statement that the approval is sufficient. Where the table says "none exists" the missing approval is a precondition, and nothing in this plan or in a `PASS_WITH_NOTES` review supplies it.

### 6.2 Acceptance tiers

Two kinds of evidence are kept apart. A result from one tier never fills a cell of the other.

| Tier | What it can show | What it cannot show | Gate and approval |
|---|---|---|---|
| O — offline, process-local | Unit, domain and contract tests on process-local fakes or in-memory adapters, and FEAT-057 composition tests. They show that an adapter honors the public contract under a scripted interleaving, state-machine rules, replay and lost-ack shapes, fail-closed behavior and lineage. | Durability, SQL isolation or constraints, real lock order or deadlock freedom, which writer wins a real race, restart recovery from stored data, read-after-commit on the finalization store, the migration graph. A fake is never used to prove durability. | G2–G7, under the offline approvals that cover the paths involved. |
| D — durable / SQL conformance | Actual store evidence: the same-store durable fence, two-session lock order, transaction rollback and recovery, the race winner under concurrent SQL transactions, the schema and migration graph, read-after-commit. | Nothing about card acceptance or BE1 integration. | G8 only. It needs its own database approval: the FEAT-057 approval excludes shared SQL/database provisioning, and the card approvals keep SQL environments separately gated. No database was run for this plan. |

An edge or boundary whose contract requires tier-D proof is `PARTIAL` or `BLOCKED` at tier O. Durable conformance does not use a fake as a substitute for the store.

### 6.3 Suggested owner-branch sequence (names are proposals, check availability before creation)

| Order | Suggested branch | Main owned increment | Merge prerequisite |
|---:|---|---|---|
| 1 | `feature/be2-01-cross-lane-lifecycle` | UoW A/S/H/B/F, stale/reject/guard/I, recovery | The per-boundary entry blockers in G2, which mirror the "Missing condition" column of §6.1 for A, S, H, B-accepted, B-stale, F and F-reject, plus D4, lock-path review and BE2-01 supplemental scope/approval |
| 2 | `feature/be2-08-cross-lane-video-lifecycle` | Participant, S/B state, codec/receipt/read model | BE2-01 API (CR08-01 entrypoint), the BE2-08 execution manifest and supplemental approval; for B-stale also BE1 adoption |
| 3 | `feature/be2-07-source-fence` | Exact X01 source fence | BE2-01 lock/fence protocol; BE2-07 revised adoption |
| 3a | `feature/be2-07-09-x05d-resolver` (only if owners adopt one) | X05d current-source resolver/fence for BE2-09 review commit and playback intent | Owner adoption recorded in `FEAT-056-be2-knowledge-script` and `FEAT-051-be2-video-review-playback`; otherwise X05d stays BLOCKED and this branch is not created |
| 3b | `feature/be2-07-09-x02-invalidation` | X02 invalidation delivery to BE2-09 | Separate X02 owner decision and approvals; does not satisfy X05d |
| 4 | `feature/be2-12-publication-bindings` | Published-content exports/invalidation | BE2-12/08/09/11 contracts adopted |
| 5 | `feature/be2-14-execution-policy` | Deny/defer, typed split, phase grants and reservation terms | Owner-supplied budget terms and BE2-01/14 CR approval |
| 6 | `feature/be2-09-video-consumers` | X05b review head/projection and X04 consumer | BE2-08 read model; adopted X05d gate before any successful review; X05c stays open |
| 7 | `feature/be2-10-failure-bridge` | X06 typed failure/disposition | BE2-01/08 terminal receipt contract |
| 8 | `feature/be2-11-publication-consumer` | X04 exact activity binding | BE2-12 public reference and BE2-11 adoption |
| 9 | `feature/be2-13-preset-dispatch` | X07 plus X08/X09 consumer binding | BE1 session authority, BE2-14, BE2-01 job contract |
| 10 | `feature/be2-cross-lane-composition` | FEAT-057 graph harness/evidence only | All included owner SHAs reviewed and available |

Names are illustrative and no branch/worktree is created by this plan. Before each branch, verify its local/remote name and base; preserve current dirty work. Keep the existing `feature/be2-backend-ai-integration` as the integration candidate unless a separately approved publication plan changes it. New card-owned changes are made in their owning feature worktree, then integrated by reviewed SHA; FEAT-057 does not edit card files. Two groups of pre-existing changes sit in this worktree and are not FEAT-057's: the BE2-01 typed-route source and test files (made under the BE2-01 supplemental approval) and the dirty or untracked card documents of `FEAT-044`, `FEAT-049`, `FEAT-050`, `FEAT-051` and `FEAT-056` (both described in G0). FEAT-057 does not own, commit or move either group, and this plan changes neither. The disposition of each group is a G0 item for its card owner.

## 7. Completion criteria and truthful finish states

`BE2_CROSS_LANE_OFFLINE_PASS` requires: all X01–X09 are `PASS`, including X05a–X05d; each test uses producer-created input and a consumer public contract; job/run/pin/attempt/artifact lineage is exact; A/S/H/B/F/reject/guard/recovery behavior has a single authoritative winner; policy, audience, source and publication revocation fail closed, and the budget-exhaustion behavior at A-time, the status read path and completion (D4) is whatever the owners adopt for those three places (the candidate invariant in §5.2 is not an exit criterion until adopted); BE2-09/10/11 consume their intended outputs; review and security/architecture/harness validators pass on the same pinned tree; and every changed owner scope is approved and reviewed.

If any edge or sub-edge is missing, unadopted, skipped, or lacks durable proof required by its contract, the overall outcome is `PARTIAL` or `BLOCKED`, never full PASS. In particular, process-local tests alone cannot upgrade X01 beyond `PARTIAL` where the accepted contract requires a same-store durable fence, and X05 cannot pass while X05d is `BLOCKED` or X05c is open. A selected Modal CPU run is optional evidence only; environment/Modal stays deferred until a separate resume instruction. Offline (tier O) evidence never stands in for tier D: durability, SQL, lock-order and race-winner claims stay `NOT_RUN` or `BLOCKED` until G8 conformance runs under its own database approval, and any statement of an "offline PASS" must say so. Provider/Lightning/runtime and live BE1 integration are outside this frame.

The BE1 code handoff additionally requires a clean, exact, published commit/PR and the BE1-owned artifact adoption in the owning BE1 record. A message, draft packet, or dirty FEAT-057 worktree is not a code handoff. Per-card statuses/acceptance remain owned by their own records and are not changed by the integration PASS.

## 8. Immediate next steps

1. Re-review this revision against its Rev5 manifest, the re-review notes (§9.2, §9.3, §9.4) and the current Rev7/Rev8/CR set. The revision-4 re-review ran in a separate read-only session; this one should also be run by a session other than the one that edited it.
2. Resolve D4, the A-time and read-path budget gates, and the numeric budget inputs/phase-reservation terms; record the decisions in the `FEAT-044-be2-ai-job-foundation` and `FEAT-049-be2-ai-policy` owning records.
3. Obtain the BE2-01/BE2-10 retry-policy and request-field mapping decisions (§4.4), and decide CR08-01: either adopt a foundation-owned shared UoW/recovery entrypoint or keep A and the foundation side of B-accepted blocked.
4. Send the BE1 artifact packet through the owner (outside this plan's execution); record adoption or keep B-stale implementation blocked.
5. Convert each blocked edge into a card-owned scope/CR and exact supplemental approval. Do not start source edits for that edge before its gate is satisfied.
6. Take the read-only snapshot of the dirty candidate with a path, size and SHA256 manifest (G0). Do not stash or commit in this scope; those need their own explicit instruction. Enter G2 for a boundary only when G1 is complete and that boundary's approval in §6.1 is recorded; otherwise it stays blocked. Keep runtime, Modal and Lightning deferred absent explicit resume.

## 9. Review dispositions

### 9.1 Review 1 disposition

Made in revision 2 and carried into revisions 3 to 5 except where §9.2, §9.3, §9.4 or an annotation below amends it. Each item is addressed **in the draft's text**. A disposition never closes an owner gate; remaining gates are listed in the last column.

| Finding | Where addressed | Gate that remains |
|---|---|---|
| P2-1 lock order | §1.2 D1 wording ("selected", review pending); §4.3 candidate rule, exceptions, current-source comparison, open items | Lock-path review; multi-pair/notice revision; outbox-claim exception; bookkeeping order; same-store fence; G8 durable evidence. |
| P2-2 boundary/completion tables | §4.1 adds H, Guard and corrected I; §4.2 adapts Rev7 §3 Table 1 and Table 2 with SHA (relabelled from "reproduces" in revision 3; added and adjusted rows are marked) | NEW-5 owner confirmation; D4; BE2-08 versioned stale CR; journal schema. |
| P2-3 budget vs eligibility | §4.1 S row (three gates, fail closed); §5.1 authorities; §5.2 six call sites | A-time and `get_job_status` owner decisions; BE2-14 typed split; D4; numeric terms. |
| P2-4 X05d/X02 | §2 graph; §3 X02/X05 rows; §3.1 definitions and rules; G1, G3, G5, branches 3a/3b/6; §7 | X05d stays `BLOCKED`; X02 needs its own approval; X05c/CR09-02 `OPEN`. |
| P2-5 A prerequisites/envelope | §4.4; §4.1 A row; G1; G2 entry; branch 1 | Retry-policy mapping (BE2-01/BE2-10); request-field and session mapping; job-type mapping; semantic-index reconciliation. |
| P3-1 X09-08 | §3 X09 row; §3.2 | X09-08 stays `NOT_IMPLEMENTED`; unsupported-type lifecycle outcome is a BE2-01 decision. |
| P3-2 FEAT ids | §1.1 map; full directory names in §4, §5, §6 | None. |
| P3-3 manifest coverage | Rev2 manifest adds owner dispositions, G0 ballot/review, card approvals, BE2-03/04 records, schema CR, source files; §4 notes stale cross-references in BE2-14 Rev3, schema CR and BE1 packet | Owning records must fix their own references (not edited here). |
| P3-4 dirty BE2-01 source | G0; §1.3; branch-table note | BE2-01 owner decides commit location/ownership. |
| P3-5 historical approvals; S/F approval | §1.2; §1.3 | Supplemental S/F/H/B-stale/F-reject/schema approvals (A and B-accepted added in revision 4; §1.3, §4.1). |
| P3-6 budget paths | §5 items 2 and 4 with Budget CR Rev2 §3–§6 | Joint CR review/adoption. |
| P3-7 B-stale | §4.1 B-stale row; §4.5 | BE1 adoption (packet `NOT_SENT`); descriptor tri-state; identity/journal CR. |
| P3-8 X05b | §3.1 X05b row; G4, G5 | BE2-08 read-model and BE2-09 projection adoption; read-after-commit proof. |

### 9.2 Re-review of revision 2: P3 notes

The notes were relayed in the owner's instruction for revision 3; the re-review report is not in the worktree. Each note was addressed in revision 3's text and the disposition is carried unchanged into revisions 4 and 5. No disposition closes an owner gate or turns a note into an owner decision.

| Note | Where addressed | Gate that remains |
|---|---|---|
| N1 budget invariants | §5.2 (row and paragraph now say *candidate invariant, not adopted*); §7 (removed from the exit criteria) | Owner decisions at A-time, the `get_job_status` read path and D4; the BE2-14 typed resource/current-use split. |
| N2 per-boundary G2 blockers | G2 entry (S, H, B-stale, F-reject, with D4 for the completion boundaries); branch-table rows 1–2; §6.1 | Each listed entry item for each boundary. |
| N3 A and B-accepted unapproved | §1.3; §4.1 A and B-accepted rows and the approval-status paragraph; G1; §6.1; §8 step 3 | CR08-01 adoption; BE2-01 supplemental approvals for A and B-accepted. |
| N4 "only exception" wording | G0 (second and third path groups); §6.3 closing paragraph | Each card owner's disposition of the dirty card documents. Not edited here. |
| N5 creation lease and CR08-01 in lock review | §4.3 table row and open-items list; G1; §8 step 3 | Lock-path review, including where the creation lease sits and the CR08-01 entrypoint. |
| N6 "reproduced" label | §4.2 intro and the "Relation to Rev7" column on both tables (added rows and adjusted wording marked) | None; Rev7 governs any difference. |
| N7 "freeze safely" | G0 and §8 step 6 (read-only snapshot with manifest and hashes; no stash or commit; G2 entry rule) | The G0 snapshot itself is not taken yet. Any stash, commit or branch step needs its own instruction. |
| N8 offline versus durable | §6.2 tiers; G2, G3, G4, G5, G7, G8 exit gates; §7 | Tier D needs its own database approval (G8). |
| N9 route-unavailable, status ladder, approvals | §3.2 (`UNSUPPORTED_JOB_TYPE` and `VIDEO_ROUTE_UNAVAILABLE` separated); §1.4 status ladder; §1.5 (no claim about the BE2-02/11/12/13 approvals; the manifest does not pin them) | The unsupported-type lifecycle outcome remains a BE2-01 decision. |

### 9.3 Re-review of revision 3: P3 notes

The three notes come from a read-only re-review of revision 3 that was run in the session which wrote it. The report was given in chat and is not saved as a repository file, so it is not hash-pinned; the notes are recorded as stated there. Verdict `PASS_WITH_NOTES` (no P1, no P2, three P3). It approves no code. No disposition below closes an owner gate.

| Note | Where addressed | Gate that remains |
|---|---|---|
| R3-P3-1: §9.1 P2-2 row still said "reproduces" | §9.1 P2-2 row now says "adapts", points to the revision-3 relabelling and keeps the pointer to §4.2 | None. |
| R3-P3-2: A and B-accepted missing from the approval lists | §1.3 closing paragraph and the G2 approvals list now name A and B-accepted together with S, F, H, B-stale and F-reject; §9.1 P3-5 row annotated. §1.2's D1 bullet is left as written, because it quotes what D1 itself says about S and F | The approvals themselves. None exists for the BE2-01 side of any boundary (its only supplemental approval is the typed route); A and B-accepted also lack CR08-01 (§4.1, §6.1). |
| R3-P3-3: §6.1 overstated path provenance | §6.1 introduction separates named-by-draft, card-list-with-inferred-assignment and inferred paths; the table marks `inferred` on the BE2-01 sets of A, S, B-accepted, F and F-reject and on the BE2-08 assignment in those rows | The owner or a reviewer must confirm or replace each inferred set in the execution manifest. |

### 9.4 Re-review of revision 4: P3 notes

The notes come from a read-only re-review of revision 4 run in a separate session. Its report is in that session's transcript and is not saved as a repository file, so it is not hash-pinned; the notes are recorded as stated. Verdict `PASS_WITH_NOTES` (no P1, no P2, four P3). It approves no code, and no disposition below closes an owner gate. The author checked notes 1–3 against the files before accepting them; note 4 is accepted in part.

| Note | Where addressed | Gate that remains |
|---|---|---|
| R4-P3-1: §6.3 row 1 and G2 listed fewer blockers than §6.1 (F absent; reservation expiry/renewal for H, execution manifests and CR08-01 for B-stale and F-reject absent) | G2 now lists all seven boundaries and mirrors the §6.1 "Missing condition" column; §6.1 gains the AP-08 execution manifest on B-stale and F-reject and the AP-14 execution manifest on H; §6.3 row 1 points at §6.1 for A, S, H, B-accepted, B-stale, F and F-reject | The listed items themselves. |
| R4-P3-2: the §1.3 sentence "For A and B-accepted none exists" read as if the other boundaries were approved | §1.3 now says no such supplemental approval exists on the BE2-01 side for any listed boundary and names the hash-bound addenda that have no execution manifest; the §9.3 R3-P3-2 row is reworded the same way | The approvals themselves. |
| R4-P3-3: §6.1 provenance overstated ("no draft names BE2-01 files"); B-stale labelled "named" although the stale CR names only some of the files | §6.1 introduction rewritten into three classes; a provenance table by row; S and F cells now read "from Budget CR Rev2 …; assignment inferred"; the B-stale cell separates what stale CR Rev2 §7 names from what it calls governing contracts and notes that two port filenames come from BE2-08 Rev3 §8 | The owner or a reviewer confirms or replaces each inferred or assignment-inferred set in the execution manifest. |
| R4-P3-4: §6.3 and §9.3 did not name F | The §9.3 R3-P3-2 row already named F; the gap was in §6.3 row 1 and G2, fixed under R4-P3-1 | None. |

## 10. Recordkeeping for this draft

This plan is a planning artifact only. It does not alter the approved FEAT-057 Rev2 scope, per-card scopes/approvals, source, tests, schema/migrations, branch, card status, acceptance, runtime gate, or publication state, and it does not edit the parent frame or its manifest. The exact planning inputs and this document's SHA are recorded in `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_REV5_20261021.json`. Revisions 1 to 4 and their manifests are preserved unchanged. Source line numbers refer to the manifest-pinned bytes. Tests and runtime were not run to write the plan. X01 `PARTIAL`; X05 `NOT_IMPLEMENTED`; X05d `BLOCKED`; X05c/CR09-02 `OPEN`; X09-08 `NOT_IMPLEMENTED`; D4 and budget values pending; Modal/Lightning/provider/database/runtime deferred.
