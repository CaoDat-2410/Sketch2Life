# FEAT-057 X01/X05 cross-lane slice plan — revision 8 draft

- Status: DRAFT / OWNER_D3_RECORDED_D4_COMPLETION_CHOICE_PENDING / READY_FOR_OWNER_DECISION.
- Parent: CROSS_LANE_X01_X05_SLICE_PLAN_REV7_DRAFT_20261021.md, SHA256 7B74AE00E5014C5B436B9FF9B0E06976D5406B2450328ED10653C200CCEABB64.
- Branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7. Worktree remains dirty; exact bytes are manifest-pinned.
- Owner D3 receipt: evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C.
- Foundation UoW scope Rev7: FEAT-044 plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV7_DRAFT_20261021.md, SHA256 BD119A05F72D311BAC299F3E940927DCE80D67DC1CD38EBE87B7D5ACC1B6EAE9.
- BE2-08 scope Rev3: FEAT-050 plan/CROSS_LANE_BE2_08_SCOPE_REV3_DRAFT_20261021.md, SHA256 66C614FF268E418F27FA4923FB7272A845F7BC7DA8BB225B8CD10032D364F801.
- BE2-14 scope Rev3: FEAT-049 plan/CROSS_LANE_BE2_14_SCOPE_REV3_DRAFT_20261021.md, SHA256 02526017042AC56224D2FF63119B0E927EFBC38DE839879632B3831B9ABDABAE.
- Source facts: manifest Rev4 SHA256 2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F. The next review-input manifest pins the new drafts and additional relevant candidate files.

This successor consolidates D1/D2/D3 and Claude rereview 3 plus rereview 4 follow-up findings. It does not change historical plans/addenda, official approvals, source, tests, schemas, migrations, acceptance, or runtime authority. It is a document/source-review candidate. No scope-review PASS is interpreted as code or supplemental S/F approval.

## 1. Owner direction and slice boundary

BE2-01 owns every lifecycle UoW; BE2-08 is a participant restricted to its own video rows. FEAT-057 owns composition only under its later exact supplemental manifest. Keep WorkerDispatchEnvelope unchanged and prove job/run/pin mapping from persisted owner APIs.

D3 C1-A requires durable BE2-01-owned budget hold with job/run BOTH QUEUED, not a new JobState or video budget state. A due/otherwise eligible retry performs its normal requeue exactly once and persists the hold with the new queued pair in the same UoW; repeated denial does not create another attempt. VideoRun attempt_id is null until S. Budget waiting cannot become dispatch loss or consume recovery allowance. Genuine consent/kill denial still cancels. BE2-14 supplies deny/defer contract only, not invented budget or execution authority.

D3 C2-A assigns authoritative stale success to B-stale, not to F-reject. One foundation commit saves job SUCCEEDED/STALE/result refs, the STALE receipt, video terminal stale/no artifact/no ready state, and verified private-stage intent. BE2-01 owns the changed stale branch; BE2-08 owns its lifecycle/codec/persistence/receipt/public-projection CR. BE1 artifacts-owner adoption is still required for exact owned descriptors, fixed reason and accepted-reference protection.

This slice remains X01, X05a/b conditional composition, BE2-08-only X09 routing and policy consumption. Do not pull X02, BE2-13 dispatch, X05c/CR09-02 or X05d resolver implementation into it.

## 2. Exact draft/CR set

| Draft | Owner | Authority |
|---|---|---|
| Foundation UoW scope Rev7 | BE2-01, video participant BE2-08 | Candidate public UoW, mapping, paired lifecycle, locks, recovery. |
| CROSS_LANE_BUDGET_DEFERRAL_CR_REV2_DRAFT_20261021.md | Joint BE2-01/14 | Typed resource defer, QUEUED hold, dispatch/ack/recovery/resume and boundaries; not adopted yet. |
| CROSS_LANE_BUDGET_DEFERRAL_SCHEMA_CR_DRAFT_20261021.md | BE2-01 | Separate schema/new-migration review candidate; no published migration change. |
| CROSS_LANE_STALE_FINALIZATION_CR_REV2_DRAFT_20261021.md | BE2-01 + BE2-08 participant | Authoritative stale branch, same-commit owned intent, classification and recovery; BE1 adoption gate. |
| BE2-08 scope Rev3 | BE2-08 | Full A/S/B-accepted/B-stale/F/reject/incident participant and versioned state/codec/receipt/projection impacts. |
| BE2-14 scope Rev3 | BE2-14 | Deny/defer contract only; no self-issued budget/execution grant. |
| BE1 artifacts adoption packet | BE1 artifacts/storage owner response required | Prepared request, NOT_SENT; no adoption claimed. |

Existing approved exact-hash A/B/typed-route subsets are historical and do not cover the expanded source/schema paths. Exact minimal implementation manifests and matching supplemental approvals are required later.

## 3. Complete boundary classification

The foundation scope and stale CR provide the full output-to-boundary and job/result/receipt/video pair tables. Key distinctions:

| Semantic outcome | Boundary / authoritative commit |
|---|---|
| Current safe successful output | B-accepted, exact artifact and accepted job/run/receipt. |
| Context-stale safe successful output | B-stale, SUCCEEDED/STALE plus video stale/no artifact and D3 intent. |
| Failure claim | F; receipt ACCEPTED acknowledges the failure, not an accepted video. |
| Consent/session/source/kill denial, unsafe output, malformed output | F-reject, separate from B; exact paired outcome and verified effects. Resource-only BUDGET_EXCEEDED at completion remains a separate owner gate. |
| Cancelled/terminal/superseded guard | Preserve winner; non-authoritative incident/intent-only, never turn an accepted run stale. |
| Temporary/invalid-state/input/normalization guard | No job/run lifecycle or authoritative-completion commit. Existing audit-only incident persistence is explicit, not silently removed. |
| Prior receipt | Exact replay or conflict; no replacement of winner. |

No transaction spans external generation. B-accepted, B-stale, F and I-incident are not dispatched solely by receipt disposition.

## 4. Budget hold, resume and source constraints

BE2-01 changes all three cancellation-on-budget branches and their dependent writer/query paths. A hold is durable metadata plus generation, with no new budget lifecycle state. Query filtering alone is insufficient: mutators recheck the current hold under the authoritative job/run locks.

The joint CR covers claim_outbox, _dispatch_one, ack_dispatch, _recover_unstarted, queued_dispatched_not_started, retry sweeps, retry callbacks and cancellation closure. Waiting cannot hot-claim/publish, create a running timer, spend dispatch-loss allowance, or mutate a later epoch through an obsolete ack/callback. Historical publication audit remains intact. Current envelope/start capability is not claimed to contain an epoch; same-active-attempt delivery still needs CURRENT persisted grant checks and unique S CAS.

A failed old attempt's resource proof cannot authorize its newly queued replacement. Actual execution/reservation proof must name the persisted new attempt before S. Reserve/settle runs outside lifecycle locks; exact cross-store validity/handoff/lost-ack remains a CR gate.

Hold endpoints are authoritative RESUMED after fresh eligibility/reservation and separate execution checks, or CLOSED with legitimate owner/eligibility/terminal lifecycle. Resume closes the hold while pair remains QUEUED until S. Maximum defer duration, what counts toward it and its deadline action are PENDING; no number/TTL/automatic fail/cancel/refund/scheduler is chosen. Expiry/renewal is a distinct reservation CR.

Current foundation retry policy has no version/hash and is dependency-injected/fixture-default; stored JSON snapshot is not exact equality to VideoPin.retry_policy. BE2-01/10 must adopt that mapping. A currently remains blocked. Missing RequestRef counterparts/job_type mapping and null session handling likewise need exact adopted contracts.

## 5. B-stale and BE1 descriptor adoption

The same-commit intent uses only artifacts-port BE1 descriptors proved produced by exact organization/job/attempt. If mapping, owner adoption or accepted-reference protection is missing, no partial stale job/run/intent commit is allowed; retain pending recovery/fail closed.

STALE_CONTEXT is a proposed fixed source-existing artifacts reason. It is not an already signed BE1 capability. The adoption packet asks for support of quarantine/keep-private refs still present in result_refs of SUCCEEDED/STALE, canonical deterministic event identity, durable delivery acknowledgement and accepted-reference arbitration.

Accepted-first cleanup is harmless to accepted references; cleanup-first requires later acceptance to revalidate exact availability/protection before committing. An old JOB_TERMINAL guard cannot bypass this. Intent durability is not physical deletion, current-use access, or permission to delete accepted output.

Stored operation/effect identity and original claim fingerprint are immutable across replay. A changed canonical input conflicts; a genuinely new authorized incident has a distinct identity. A durable stage/reject-operation journal is still a versioned recovery/schema gate.

## 6. Source fence, read model and policy gates

X01 stays PARTIAL: BE2-07 currently has no adopted same-store source fence. Exact resolve/process-local coordination is not held-through-finalization. Inventory all bundle/context/audience/editorial/policy/profile/rights/source/artifact inputs, owner keys and invalidators. BE1 owns ArtifactDescriptor.fence. Durable serialization needs separately authorized PostgreSQL two-session evidence for both winner orders.

BE2-08's versioned CR changes its video-owned stale axis, codec format, save terminal set, _receipt, public schema/projection and blind state-equality checks together. Existing non-accepted receipt shape is not already compatible. AR01/AR05 exclude terminal stale/no artifact from finalized-artifact responses; historical accepted-but-later-ineligible output is distinct. Receipt provenance, exact identity, visibility and read-after-commit still need separate owning-card adoption.

BE2-14's revised slice supplies deny/defer only. Eligibility, worker execution and budget/concurrency proof remain distinct. Current accounting phase enum has no assumed start phase; mapping/version changes, reservation expiry/renewal and actual owner terms remain open. No provider runs while a required gate is unknown, false or held.

X05d remains BLOCKED. X05c/CR09-02 stays OPEN; playback intent does not prove a session/access grant.

## 7. Complete P3 crosswalk for the next review

| Finding | Required correction now present in scope/CR set |
|---|---|
| F-04 key / source pin | Media formula/public schema/completion fingerprint source pinned; adapter independently reconstructs and compares key, never echoes caller; nonaccepted needs durable stage journal. |
| F-05 event_id/reason | Original fingerprint timing, stored immutable decision/effect identity, changed-input conflict vs new-operation intent, no fake completion-slot receipt; audit-only incident explicitly retained. |
| F-06 notice | ID discovery is not authority; locked tenant/CANCELLABLE_STATES/OR predicate and paired revision recheck; preserve atomic max/idempotent COMPLETE semantics. |
| F-06 complete fence set | Lock all ordered job/run pairs, hold complete deduplicated sorted union once, restart on late fence; wrapper-order statement limited to SqlAiJobUnitOfWork. |
| F-07 fence owner | BE1 artifact owner; editorial_revision named; fixture remains ASSUMED_CONTRACT. |
| F-08 job_type | Persisted job/message/configured typed route mapping before S, no inferred field on VideoRun. |
| F-10 AR05 | Terminal stale/no artifact excluded; not confused with later current-use revocation of historical accepted output. |
| F-11 errors | Full write/stale/immutable/terminal/invalid-transition/attempt/corrupt/receipt/infrastructure taxonomy; errors escape UoW, rollback first, corrupt never replay. |
| N-04 retry policy | Foundation source/status/version/hash limitations explicit; A cannot pass before BE2-01/10 CR. |
| N-05 owning scope | Old A/B draft/blank header hash preserved as history; BE2-08 successor adds domain/codec/full lifecycle and separate public schema gates. |
| N-05 nonexistent adapter | Historical claim of cross_lane/knowledge_video.py corrected; actual knowledge_script_video.py is source-reader only, not lifecycle-UoW composition. |
| N-06 model | All retry/fail/block/timeout/stale transitions and queued attempt-id invariant included in BE2-08 CR. |

Earlier wrong disposition path was repaired by exact historical hash recovery and preserving later bytes under a separate successor name. No historical validator receipt was changed.

## 8. Revision and authority divergence

Historical FEAT-057 Rev4/Erratum1/Rev5/Rev6 and FEAT-044 scope Rev4/Rev5 remain immutable. This revision explicitly supersedes the all-nonaccepted→reject simplification and earlier FAILED_RETRYABLE-waiting proposal because D3 requires QUEUED. Earlier design-direction G0 PASS does not mean later lifecycle scope review passed.

The dirty typed dispatcher exists and routes video messages but does not prove committed S or persisted job/run/pin composition. X09-08 remains NOT_IMPLEMENTED. Source references use manifest-pinned files/functions rather than stale line numbers. Existing governing approved index fields remain historical approved scope; the latest candidate entry is labeled draft, not silently promoted to approved.

## 9. Planned sequence and actual next gate

1. Independently review D3 alignment, scope/CR consistency and the rereview-3 findings plus rereview-4 NEW-1 through NEW-5 against the exact pinned inputs.
2. Adopt the actual missing owner contracts: BE1 descriptor/quarantine/accepted protection; BE2-01/10 retry policy; exact persisted mapping; video lifecycle/public projection/receipt; hold schema/reservation/phase/bound terms; source fence when a durable X01 claim is desired; artifact-read provenance.
3. Freeze exact per-card source/test/schema manifests and obtain separate supplemental S/F/schema approvals. A document-review PASS does not do this.
4. Implement only approved offline pieces; run focused owning-card suites and FEAT-057 composition on one pinned tree; review/fix/retest. No fake is an actual owner adoption.
5. PostgreSQL conformance, provider/server/runtime/Modal/Lightning and full-card acceptance remain separate gates. A BE1 status/design handoff may name gaps; it cannot claim BE2 fully connected.

Prior Modal 296/296 remains only the exact pinned X01 plus adjacent BE2-07/08 offline package; it proves no durable SQL, provider or full BE2-01–14 runtime. No rerun is authorized here.

No source/test/approval/schema change, stage/commit/push/merge or test/runtime run occurred for this draft. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; card acceptance unchanged.

## 10. Rereview 4 findings and owner gate

Claude's D3 rereview is preserved at evidence/notes/CROSS_LANE_UOW_CLAUDE_D3_REREVIEW_REPORT_20261021.md, SHA256 92BE229378A2DE06BAEED1FC6F675EA15FED338892A002A833F81F6972B44C12. It confirmed all 81 review-manifest entries and closed the original two P2 findings in draft, then raised one new P2 and four P3 points.

- NEW-1 (P2): completion-time BUDGET_EXCEEDED is not covered by C1-A's three pre-execution branches. No generic cancel/quarantine, acceptance, settlement, refund, retry or rerun is inferred. Owner choice is pending in evidence/notes/CROSS_LANE_UOW_OWNER_D4_COMPLETION_BUDGET_BALLOT_DRAFT_20261021.md. This plan does not select an outcome.
- NEW-2 (P3): only validated output reaches context-stale classification; malformed output is rejected first. Descriptor FOUND/ABSENT/UNAVAILABLE must be distinct. Unavailable/unmappable refs fail closed; no-target intent needs explicit BE1 adoption.
- NEW-3 (P3): FEAT-044 budget CR Rev2 and FEAT-049 BE2-14 scope Rev3 agree: ai_policy_use schema/port/service are primary deny/defer candidates; accounting schema/port are conditional inputs only for a separate adopted reservation/phase contract.
- NEW-4 (P3): stale CR Rev2 proposes versioned deterministic operation_id/payload_hash/event_id, immutable replay reason/refs and distinct authenticated operation id for a new incident. Canonical encoding and journal schema remain gates.
- NEW-5 (P3): temporary -> no commit means no lifecycle/authoritative outcome commit; audit-only incident persistence remains separate. This conservative interpretation is marked for owner confirmation.

The previous rereview prompt had a typo in the FEAT-057 folder path. This successor uses the actual offline-integration path. D4 is pending; no source/schema/test/approval follows. The package is not ready for implementation approval until the completion-time budget disposition is resolved.

Earlier approvals and historical plans remain unchanged. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; ENV deferred.
