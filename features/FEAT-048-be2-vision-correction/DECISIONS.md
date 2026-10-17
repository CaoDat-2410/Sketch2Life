# BE2-02 component decisions —2026-10-16

## Current publication re-review —2026-10-17

PUBLICATION_PLAN_REVIEW_PASS, pending explicit owner execution instruction. Root independently
verified37-path coverage, groups6/17/11/3, byte-preserving Git filters/negative controls and all
reviewed source/authorization/golden anchors. The earlier CRLF/hash and current-routing issues
are resolved; detailed result is the current entry in evidence/notes/C2_PUBLICATION_PLAN_20261017.md.
No stage/commit/push, code change, new checkpoint or full-card closure by this review. Earlier
dated review/disposition entries below are historical. BE2-01 remains WAITING_STUDIO.

All choices below are **PROPOSED_FOR_C1_APPROVAL**, not production adoption or role-owner sign-off.

| ID | Proposed choice | Reason / boundary |
|---|---|---|
| D01 | Additive strict DATA-22/CMD-34 DTOs0.1-candidate | Foundation ShapeSpec is shallow; preserve legacy V1/V2 and existing fixtures |
| D02 | Immutable original observation, append-only corrections; analysis aggregate CAS revision | UC-018 provenance; request/context/job revisions stay separate |
| D03 | Bound Child device submits own intent/proposal; scoped Teacher confirms authoritative meaning | Conservative interpretation of UC-018 actor wording; exact candidate states must be documented before code |
| D04 | Narrow correction-specific authority/source/admission/lineage ports and fakes | READ_JOB does not authorize correction; no direct BE1 DB reads |
| D05 | Fake UoW commits mutation+receipt+invalidation intent atomically, CAS one winner | CMD rules; real DB/fence/event delivery remains NOT_RUN/ASSUMED_CONTRACT |
| D06 | Additive offline bridge wraps existing V2 adapter with injected transport | Reuse actual seam without provider/network/GPU/new dependency |
| D07 | Source-only admitted render, provider_context_mode=image_only | No typed context endpoint exists; do not repurpose adult narration as Child intent |
| D08 | Separate checkpoint checksum, rendered-image hash/provenance and trusted admission binding | JSON checkpoint is not an image; never manufacture PASS |
| D09 | Validate response correlation/image/profile/catalog/config/model provenance and preserve whole original result | Existing identity checks are incomplete for new lineage; lexical pass is not full moderation |
| D10 | Isolated POST CMD-34 fixture only, no production router mount/new public GET | Verify semantics without claiming real auth/API adoption |
| D11 | C1 has no new infra/dependencies; explicit remaining full-card handoff | Component success is not full BE2-02 DONE |

## Approval —2026-10-16 19:18 +07:00

User approved planrev1 C1_COMPONENT_OFFLINE, D01–D11 and V01–V17 verbatim (approvals/TASK_APPROVAL.md,
plan SHA256 f4733c88…, snapshot plan/PLAN_REV1_APPROVED.md). D01–D11 are now **APPROVED_FOR_C1**
component candidates; still not production adoption or BE1/P1/P4 sign-off.

## C1 concrete candidate choices (recorded before code)

Routine refinements inside D01–D11; every value below is `0.1-candidate`/PROPOSED.

**Module map (D01/D06/D10).** `domain/vision_analysis.py`; `contracts/schemas/analysis_results.py`;
`application/ports/vision_analysis.py`; `application/services/vision_analysis.py`;
`infrastructure/vision_analysis/{fakes,job_lineage,legacy_v2}.py`;
`interfaces/http/routers/analysis_corrections.py`; `interfaces/http/analysis_corrections_fixture_app.py`.
Error envelope reuses BE2-01 `CollaborationErrorV1`; clock/ids fakes reuse BE2-01 fakes.

**Text and number bounds (D01).** ShortText = NFC + trim, 1–128 code points, no control characters
(SRS LIMIT_TEXT_SHORT=128 PROPOSED). LongText = NFC + trim, 1–4000 code points, only `\n` allowed
as control (LIMIT_TEXT_LONG=4000 PROPOSED). `intended_objects` 1–16 unique ShortText (case-folded
uniqueness; 16 is a technical payload bound, not pedagogy). `correction_reason` ShortText required.
`expected_context_revision` strict int ≥0. `child_explanation` LongText or null: omitted and explicit
null are the same "no explanation" value and fingerprint identically; empty/blank is 422, never null.
Confidence = null or strict finite int/float in [0,1]; bool, string, NaN/inf, out of range rejected.
CMD-34 body ≤32 KiB (413). Unknown fields are rejected, so payload cannot set actor/author/role/org/
status/revision/meaning; 422 `FIELD_NOT_ALLOWED` for extras, `FIELD_VALIDATION_FAILED` otherwise.

**Records and states (D02/D03).**
- `VisionObservation`: immutable original typed observation (all entities/actions/relations/themes/
  ambiguous regions), evidence and moderation, `observation_sha256` over its canonical form. The
  repository port has insert/get only — no update path.
- `AnalysisHead`: `analysis_id`, `analysis_revision` (starts 1, +1 per correction/invalidation),
  pinned scope/lineage/source/context, `accepted_status ∈ {accepted, stale}` with `status_reason`,
  ordered `correction_refs`, `current_meaning_ref`. Rejected outcomes are never stored.
- `MeaningCorrection`: immutable, append-only; `kind ∈ {child_proposal, teacher_confirmation}`;
  `meaning_status` fixed at creation: child_proposal→`proposed`, teacher_confirmation→`confirmed`;
  author = server-resolved principal/role/participant/turn; `correction_version` = analysis revision
  it created. `effective` is derived: only the head's `current_meaning_ref` (latest teacher
  confirmation) is effective; older confirmations are superseded by pointer, never rewritten.
- `basis_correction_ref` (N/C, candidate addition for UC-018 attribution): Teacher only; must name a
  child_proposal of the same analysis. `child_explanation` only from the bound Child device; a
  Teacher-sent explanation is `FIELD_NOT_ALLOWED` (no misattributed child words).
- Downstream meaning: confirmed concept only when the analysis is accepted, its context/source are
  still current and a teacher confirmation exists; otherwise model candidates stay candidates and
  child proposals stay proposals. A confirmation is a meaning record, not a DATA-24 review, and does
  not approve a Sketch, session or other analysis. Imagined concepts are `intended_concept`, not facts.
- ETag `"analysis:<analysis_id>:<analysis_revision>"`; another family/id/revision is 412.

**Ports and fakes (D04).** Source (opaque `input_snapshot_ref` → checkpoint + render metadata, render
bytes), admission (trusted receipt for exact render ref+hash), authority (verified principal + action
→ bound actor or reason), context (current context revision, purpose/consent/session eligibility,
authoritative contributor age), lineage (BE2-03 assistance pin; BE2-01 job view, read-only),
repository/UoW, observation provider, clock, ids. Actions: `propose_intent`, `confirm_meaning`,
`read_analysis`; READ_JOB is not correction authority. Candidate `input_hash` = canonical SHA256 of
{snapshot_ref, checkpoint id/epoch/revision/checksum, render ref/sha256}; the real BE2-03 formula is
ASSUMED_CONTRACT. Age gate uses `validate_age_months` (36–155), never `domain/child_age.py`.

**Observation flow.** lineage pin → existing (job, attempt) analysis replay → source binding →
admission → input hash → current context/eligibility/age → provider context mode → one provider
call → re-check lineage/eligibility/context/source. Pre-provider failure: no call, nothing stored.
Provider failure/unsafe/malformed: typed failure, nothing stored. After the call: cancelled/
superseded/terminal job or revoked consent/grant → rejected, discarded; context/source moved →
stored `stale` (pinned original kept for explicit reference only); else `accepted`.

**Correction flow (D05).** Guard order: principal → analysis exists in caller org (else 404) →
disclosure (`read_analysis` + consent effective; revoked 403, out of scope 404) → receipt lookup
(identical replay returns the original body with `Idempotency-Replayed: true`, ignoring If-Match,
turn and status; different payload 409 IDEMPOTENCY_PAYLOAD_MISMATCH) → action authority (device:
bound open current turn, own participant, same canvas/session/group; teacher: scoped grant) →
eligibility → expected context and analysis applicability (409 STALE_CONTEXT) → If-Match (428/412)
→ role field rules → one write: re-read, CAS, append correction, receipt, invalidation intent.
CAS loser gets 412 with nothing staged; injected commit failure is 503 DEPENDENCY_UNAVAILABLE with
nothing persisted and no receipt reserved. Key scope (organization, principal, `AnalysisCorrection`,
analysis_id, key). Fingerprint covers the normalised semantic payload, not If-Match.
Invalidation intent: deterministic `event_id`, analysis id, previous/new revision, reason
(`child_intent_proposed`, `teacher_meaning_confirmed`, owner source/context/consent change), correction
ref; committed with the mutation, delivery NOT_RUN (no event platform).

**Bridge (D06/D07/D09).** Wraps `LightningVisionV2Adapter.understand` (never
`understand_with_narration`) with a recording `JsonTransport` wrapper; refuses `UrllibJsonTransport`
under C1. Refuses before transport: typed-context request, processing/derived image, non-PNG/JPEG,
admission not bound to exact render ref+hash or not PASS. Legacy `media_validation` is populated
from that trusted receipt only. After the call it checks correlation, source image, profile,
canonical catalog hash, config hash, adapter version, model provenance, policy versions and raw
confidence types; any mismatch is `OUTPUT_MALFORMED`. Outcome map: INPUT_NOT_VALIDATED→
`SOURCE_REJECTED`, VISION_TIMEOUT→`PROVIDER_TIMEOUT`, VISION_PROVIDER_FAILURE/MODEL_UNAVAILABLE→
`PROVIDER_ERROR`/`PROVIDER_UNAVAILABLE`, VISION_SCHEMA_INVALID→`OUTPUT_MALFORMED`,
PROHIBITED_CLAIM_DETECTED→`UNSAFE_CONTENT`; never retried. Object candidates come from entities only
(label.value + nullable confidence + observation ref). Evidence kind `offline_legacy_bridge` implies
`provider_context_mode=image_only`; the synthetic fake provider may accept the typed envelope and is
labelled `synthetic_fake`. Moderation: lexical regression passed/not_executed, comprehensive
moderation `not_run`, Child visibility `withheld`.

**Fixture API (D10).** POST `/api/collaboration/v1/analysis-results/{analysis_id}/corrections` only,
fixture principals, 200 + ETag; Teacher projection carries original candidates/corrections/authors;
device projection carries refs/status only (no labels, confidence, uncertainty, evidence, moderation,
age, Teacher text). No production mount, no GET.

## C1 implementation notes —2026-10-16 (within D01–D11)

- If-Match uses strong comparison: a weak `W/` tag, a list or `*` is 412 (refines the ETag rule).
- The fake store's injected commit failure applies only to a unit of work that staged a write.
- Legacy F-01 (V2 adapter `OSError` branch builds an invalid V2 failure and raises) is contained
  by the bridge as `PROVIDER_ERROR`/`LEGACY_ADAPTER_CONTRACT_ERROR`; the adapter is unchanged
  because C1 preserves legacy behaviour. A fix needs the legacy owner's decision.
- Consent/purpose revoked while the provider ran discards the result (nothing stored) instead of
  storing it stale, because keeping child-derived output without current consent is not allowed.
- H-AI-REVIEW examples are generated deterministically and pinned by a test, not hand-written.
- Evidence: evidence/notes/C1_IMPLEMENTATION_EVIDENCE.md; handoff evidence/notes/H_AI_REVIEW_HANDOFF.md.

## Request history and stop

User requested BE2-02 preparation in a separate branch while01 waits for Studio, then asked for
requirements and a Claude-ready work prompt. These authorize planning only. No backend code or
approval was fabricated. Upon actual approval record its exact text, plan revision/hash, scope
and timestamp before code; routine choices inside that scope do not need repeated approval.

Remaining: additive real typed provider-context protocol; model/profile/serving/license/budget
adoption and measured quality; real BE1 snapshot/authority/turn/context/admission adapters;
persistence/runtime strategy/evidence, live API/P4 composition and independent review.

## Codex independent C1 review —2026-10-16

Review disposition NEEDS_REVISION: C1-R01–R06 remain OPEN (2 P1/4 P2).
See evidence/notes/C1_CODEX_REVIEW_20261016.md for reproduced cases, source locations
and required behavior. The independent focused suite passes 174/1 skip, but six
additional service invariant assertions fail and bridge/domain probes demonstrate
scope, contract and provenance defects. Existing PASS results remain historical
test outcomes; they are not an independent acceptance of the affected guarantees.
N01 body-buffering limit is a non-blocking P3 note. Real owner fencing and a mutable
foundation job hash probe are qualified residuals, not new required scope.
This is a reviewer disposition, not a new owner decision/approval or production
adoption. Keep D01–D11 and plan snapshot/approval intact; fixes then re-review C1.

## C1 review-fix candidate choices —2026-10-16 (within D01–D11; FIXED_PENDING_CODEX_REVIEW)

- **R01 (D02/D05).** Observation replay keeps the stored analysis identity and never calls the
  provider or mutates anything, but its authority is computed now: full eligibility gate first
  (`rejected` + gate code), then stored stale status, current context revision (`stale`/
  `context_changed`) and current source hash (`stale`/`source_changed`). Applies to the early and
  raced-winner replay. Replay does not persist staleness; owner notices still do. CMD-34 receipt
  replay is unchanged (current disclosure, then the original body/version/event).
- **R02 (D04).** After the provider call the complete `eligibility_code` gate (consent, purpose,
  active session, every audience age 36–155, unknown age fails) runs before acceptance; any gate
  failure is `rejected` and nothing is stored. Context/source movement still stores `stale`.
- **R03 (D04).** Candidate mapping of foundation `JobScope` to the trusted assistance pin:
  `session_id` = pin session, sorted `subject_refs` = sorted audience participants, `purpose_code`
  = pin purpose, `target_id` = assistance id. Mismatch is `JOB_SCOPE_MISMATCH` before provider and
  storage. Class/canvas are not foundation job fields and are not added; BE2-01 code unchanged.
- **R04 (D01/D09).** Shared domain constants `OBSERVATION_REF_MAX=120` (OpaqueId-sized) and
  `OBSERVATION_COLLECTION_MAX=256`, used by the contracts. `observation_bounds_violation` checks
  every observation id/reference (pattern, length), entity ShortText labels, candidate count,
  unknown-confidence refs and ambiguous regions before acceptance, in the bridge (typed detail) and
  again in the service for any provider. Violations are `OUTPUT_MALFORMED`; nothing is truncated,
  rewritten or stored. Boundary values 120/256 stay accepted.
- **R05 (D02).** `AnalysisRecordV1.corrections` has no count cap: append-only history is projected
  complete. Rationale: the cap was an arbitrary projection bound contradicting an unbounded,
  valid command path; truncation would lose attributable history and a business limit or paging
  platform is outside C1. Paging belongs to a later persistence/API decision.
- **R06 (D09).** Providers return `result_document` (canonical JSON of the whole typed result) whose
  SHA256 must equal the evidence `result_sha256`. The service retains it as an immutable
  `ProviderResultRecord` under `result:<analysis_id>` (insert-only port), committed in the same
  unit as observation and head, so failed writes publish nothing. `resolve_provider_result` is the
  trusted Teacher/internal resolver (same disclosure; device FORBIDDEN, others concealed 404) and
  re-verifies the hash. Never in a Child projection or public route; in-memory only in C1.
- N01 (body buffered before the 32 KiB check) stays a recorded P3 limitation, not changed here.
- Evidence: evidence/notes/C1_REVIEW_FIX_EVIDENCE_20261016.md.

## Codex C1 re-review disposition —2026-10-16

Reviewer disposition: R01/R02/R03/R05/R06 CLOSED_C1_COMPONENT_SCOPE;
R04 remains OPEN (P2), so C1 NEEDS_REVISION. Python match($) accepts final newline
while DTO rejects; truthy filtering skips empty optional action refs. Both remain
the original R04 producer/contract mismatch. Small guard/regression fix only;
no new acceptance/authority/owner-fence/adoption or full-card closure decision.
Evidence: evidence/notes/C1_CODEX_REREVIEW_20261016.md and matching metrics.

## C1-R04 follow-up —2026-10-16 (FIXED_PENDING_CODEX_REVIEW)

Refines the R04 choice: `observation_bounds_violation` checks every non-None reference (an empty
string is a reference, only `None` is absent) with full-string `fullmatch` against the DATA-22
`ObservationRef` pattern, so a trailing newline or empty optional action ref is `OUTPUT_MALFORMED`
before storage. No stripping, dropping, DTO relaxation or legacy/foundation change.
Evidence: evidence/notes/C1_R04_FOLLOWUP_EVIDENCE_20261016.md.

## Codex R04 final closure —2026-10-16

Reviewer disposition: R04 CLOSED_C1_COMPONENT_SCOPE after fullmatch/non-None
reference guard fixes and meaningful negative/positive regression proof. All six
review findings are closed within C1. Code review PASS_WITH_NOTES; Pillow-dependent
checks remain NOT_RUN, N01 remains non-blocking, no owner acceptance/adoption or
full-card closure inferred. No extra `_require_sha` fix batch opened by review.
Evidence: evidence/notes/C1_CODEX_R04_CLOSURE_20261016.md and matching metrics.

## Remaining verification inventory —2026-10-16

Observation, not owner approval: existing base-Python Pillow can be loaded in the
test process without installing dependencies;7 V2 server tests passed. Production
route walk still requires the already-declared python-multipart package, absent in
both inspected interpreters. No installation authorized or performed. Proposed next
action is a feature-local ignored dependency target, not a shared-venv modification
or new C2 scope. Evidence: notes/C1_REMAINING_CHECKS_20261016.md under evidence.

## Completion of named C1 verification —2026-10-16

After the narrow environment continuation was described, user directly instructed
“tiếp tục đi”. This authorized installing only the already-declared python-multipart
into ignored feature-local test dependencies and running the missing checks;
shared venv and original C1 approval/plan remain unchanged. No code scope extension.
Result: focused233/233, V2 server7/7, separate foundation route1/1 PASS,0 skips.
C1_VERIFICATION_COMPLETE_PENDING_OWNER_ACCEPTANCE. No owner acceptance, production
adoption, full-card closure, new card or Git publication inferred. Evidence:
evidence/notes/C1_FINAL_VERIFICATION_20261016.md and its metrics.

## User resume order —2026-10-16

Direct user instruction: “Xong cái này note lại đi mai lighing bth làm xong task 1
xong làm tiếp task 2 này”. Prioritize pending BE2-01 Studio verification and review
when Lightning becomes usable; return to BE2-02 C2 planning after that. No new C2
approval, Q1–Q5 decision, implementation or runtime PASS inferred. C2 draft retained
unchanged locally; C1 accepted/pushed checkpoint remains98876fe. No Git publication
or provider/service action authorized/performed by this note.

## C2 preparation —2026-10-17

User: “th chuẩn bị c2 đi lên plan cho tôi sau đó lấy prompt cho claude làm”. Authorized
scope is plan/prompt preparation while Lightning is unavailable, not C2 implementation.
Plan/C2_TYPED_CONTEXT_PLAN.md revision2 is DRAFT / AWAITING_OWNER_APPROVAL. Q1–Q5 remain
recommendations: anonymous synthetic per-member bands; no Child text; defer feedback/action
inputs explicitly; offline new client contract; coherent fixture revision/digest checks.
Source/code review added the internal/provider boundary, distinct digests, typed0.2 contracts,
revocation versus stale behavior, immutable authorized receipt replay and qualified concurrent
deduplication. Review note: evidence/notes/C2_PLAN_REVIEW_20261017.md. Templates are local,
not approvals. Original C1 approvals/plan preserved; no backend/test/service/Git changes.

## C2 approval —2026-10-17 11:20 +07:00

User approved C2_TYPED_CONTEXT_OFFLINE (plan revision2, C2.1–C2.5, C2-A01–A14, SHA256
4b339514…) verbatim in approvals/C2_TASK_APPROVAL.md; approved bytes
plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md. Owner selected Q1–Q5 exactly as recommended:
Q1 anonymous per-member bands (exact months internal; fixture-completed-years-v1 test-only,
NOT_PEDAGOGICALLY_ADOPTED); Q2 no Child text, Teacher topic + trusted request enums only; Q3
feedback/confirmed meaning/action summaries deferred as provider inputs; Q4 new client contract +
injected offline transport, no server/prompt/endpoint call; Q5 coherent fixture snapshot/revision/
digest, real owner adapter is handoff. Component candidate only; C1 approval/plan/acceptance kept.

## C2 candidate technical choices —2026-10-17 (within plan rev2; PROPOSED, not adopted)

- **Modules.** `domain/vision_context.py` (snapshot, gate, projection, digests, band policy,
  capability); additive `TypedContextBinding`, `EvidenceKind.offline_context_adapter`,
  `ObservationEvidence.context_binding` and `AnalysisHead.typed_binding` in `domain/vision_analysis.py`;
  `VisionContextSourcePort` in ports; `contracts/schemas/vision_context.py` (client 0.1-candidate)
  and `analysis_context_results.py` (records 0.2-candidate); `infrastructure/vision_analysis/
  context_adapter.py`. Pure pre-checks/request build/outcome map/verification/mapping were
  extracted from `legacy_v2.py` as shared functions; bridge behaviour unchanged.
- **Contract versions.** `VisionTypedContextV1`, `LightningVisionContextRequestV1/ResultV1` are
  `0.1-candidate` (new client contracts, path `/v1/vision/context`, no server). Typed DATA-22
  records are sibling `0.2-candidate` (`AnalysisWorkerCandidateV2`, `TypedProvenanceV2`,
  `AnalysisRecordV2`, `TypedContextBindingV2`) reusing unchanged 0.1 sub-models. Canonical rules
  version `vision-context-canonical-v1`.
- **Request enums (source-undefined, candidate).** reason ∈ {describe_drawing,
  support_meaning_check}; target_kind ∈ {whole_canvas, contributor_strokes}; requested_level ∈
  {brief, standard}. From the trusted owner port only.
- **Field use.** Provider fields `teacher_topic`, `audience_age_bands`, `request_enums`; every
  member must permit all three plus provider transfer, consent and purpose; one denial refuses the
  whole call (no partial payload). Child text, feedback, confirmed meaning, actions, identities,
  exact ages and consent records are not contract fields (extra=forbid).
- **Null/absent.** Every typed-context key is required; `teacher_topic` is null only when the
  owner reports no topic, never "". Bands are sorted lexicographically, one per member,
  duplicates kept, 1–64 members (technical bound).
- **Digests.** payload_digest = canonical SHA256 of the exact `VisionTypedContextV1` document.
  context_digest = canonical SHA256 of rules version, full scope/request/source binding, context
  revision, session state, members sorted by id (exact months, provenance/permission revisions,
  consent record ref, transfer, sorted fields), topic provenance, request enums, policy ref/version,
  field-policy revision and payload_digest. No self/time/correlation fields. A strict type walk
  refuses floats/NaN/non-string keys/unknown types before the foundation canonical JSON.
- **Gate order.** C1 lineage/replay/source/admission/input hash/eligibility → static capability
  (equality with the C2 capability; mismatch = CONTEXT_MODE_UNSUPPORTED before any snapshot read,
  image load or call) → owner snapshot → duplicates (snapshot, members, pin, old port) → audience
  bound/match → scope → request → source → policy/rules → pinned revision → session → each member
  (age 36–155 + band, consent/purpose, transfer, fields) → old/new port agreement.
- **Post-call.** Any typed refusal (including port disagreement/unavailable/malformed) rejects and
  stores nothing; revision movement or same-revision context-digest movement stores the original
  `stale` (`context_changed`) with its original binding; source movement stays C1 `source_changed`.
- **Reads.** Replay rejects on a current typed refusal, else stale on revision/digest movement;
  `_applicable` (downstream meaning, new corrections → STALE_CONTEXT) requires the current digest to
  equal the pinned one. Accepted CMD-34 receipts replay after the unchanged disclosure check; a
  transfer-permission revoke is not a disclosure revoke.
- **Shared C1 hardening.** `eligibility_code` now refuses duplicate participants in the audience or
  the old port's age facts before `dict()` (`AGE_NOT_SUPPORTED`), closing a last-duplicate-wins
  path; it applies to image_only too. Fake CAS treats the binding as immutable.
- **Adapter.** Reuses `LightningVisionV2Adapter` unchanged through an intercepting transport: the
  V2 body (no narration hint) is wrapped, validated, posted once; the wrapper is validated in
  strict JSON mode and every echo compared; the nested V2 result goes through the C1 verification.
  The WHOLE wrapper JSON (after a JSON-native check) is retained/hashed. Real HTTP transport refused.
- **Seam supersession.** C1 fake-only `ObservationContext` is replaced by `ProviderTypedContext`.
  `test_v15_provider_never_receives_age_or_child_content` now asserts the new exact allowlist
  (projection/binding field sets, no ids/ages/Child text); actual wire bytes are checked in
  `test_vision_context_adapter.py`. The bridge's typed-refusal test builds the new type; its
  assertions are unchanged. No other C1 test or golden changed.
- Evidence: evidence/notes/C2_IMPLEMENTATION_EVIDENCE_20261017.md.

## C2 Codex review —2026-10-17

CODE_REVIEW_PASS_WITH_NOTES, no actionable new finding in the approved offline component.
Root independently reproduced657 collected/652 passed/5 pre-existing legacy skips; ruff and
strict mypy PASS on16 paths. Three same-family delegated area reviews and9 additional adapter
negative probes found no blocker. Review: evidence/notes/C2_CODEX_REVIEW_20261017.md and matching
metrics. Historical stored accepted_status/receipt is distinct from current downstream authority;
fake concurrency and nested legacy DTO behavior do not imply real owner/DB/model guarantees.
Owner C2 component acceptance remains pending; no publication, new batch or full-card closure.
Source/tests/approvals/approved plans unchanged by review; BE2-01 remains WAITING_STUDIO.

## C2 owner acceptance —2026-10-17 11:59 +07:00

User accepted C2_TYPED_CONTEXT_OFFLINE in offline component scope on plan revision2 and
CODE_REVIEW_PASS_WITH_NOTES (verbatim approvals/C2_COMPONENT_ACCEPTANCE.md). The C2 candidate
technical choices above are now ACCEPTED_FOR_C2_COMPONENT, still not production adoption,
pedagogical band adoption or BE1/P1/P4 sign-off. Codex review notes remain open limits. The same
message requested only an inventory and commit plan (evidence/notes/C2_PUBLICATION_PLAN_20261017.md);
no stage/commit/push/merge/deploy or next checkpoint. Approvals and approved plans unchanged.

## C2 publication plan Codex review —2026-10-17

Four-commit grouping accepted as a coherent whole-file split; exact36-path coverage and all
reviewed code/approval/golden hashes independently match. Execution NEEDS_DOCUMENT_REVISION:
three metrics are CRLF and LF normalization would break the review's implementation-receipt
hash. Proposed exact-path .gitattributes preservation makes37 paths, still four commits.
Current handoff/index status also needs acceptance routing. Details at the top of
evidence/notes/C2_PUBLICATION_PLAN_20261017.md. No code/index/HEAD/approval change, stage,
commit or push. C2 component acceptance stands; full card NOT_DONE, BE2-01 WAITING_STUDIO.

## C2 publication-plan review resolution —2026-10-17

Codex publication review: NEEDS_DOCUMENT_REVISION (CRLF in three C2 metrics would be normalized
and break the pinned 68aa985f… receipt hash; stale current-state routing). Resolution, on the
user's direct instruction: keep the reviewed bytes and add three exact-path
`-text whitespace=cr-at-eol` rules to `.gitattributes` (existing hash-preservation convention, no
broad rule, no regeneration); route handoff/evidence index to the review and owner acceptance and
mark older checkpoint headings historical. Plan now 4 commits / 37 files with `.gitattributes` in
commit 1. Details and checks: evidence/notes/C2_PUBLICATION_PLAN_20261017.md "Review resolution".
No stage/commit/push; acceptance and approvals unchanged.

## C2 local publication —2026-10-17 12:38 +07:00

Owner approved executing the re-reviewed plan (4 commits / 37 files) with local staging/commits.
Current publication lines in CONTEXT/STATUS/evidence README and the two shared ledgers were synced
inside their approved commit groups (no extra status commit); dated history and the reviewed plan
note, approvals, approved/working plans and pinned metrics keep their bytes. Commits 52bf84f, 164575c,
then records and routing commits; not pushed.
