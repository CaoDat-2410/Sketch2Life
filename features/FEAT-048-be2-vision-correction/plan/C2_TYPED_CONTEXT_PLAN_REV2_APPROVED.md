# BE2-02 C2 — typed Vision context, offline component

- Revision: 2, 2026-10-17, Codex source/code review and preparation.
- Status: DRAFT / AWAITING_OWNER_APPROVAL. Implementation NOT_STARTED.
- Checkpoint: C2_TYPED_CONTEXT_OFFLINE; full BE2-02 remains IN_PROGRESS / NOT_DONE.
- Baseline: `feature/be2-02-vision-correction`, pushed HEAD `98876fe762a61e64b61980cd0634415e6f5e1dfb`.
- Feature: `features/FEAT-048-be2-vision-correction`; keep the existing task worktree/branch.
- Authority: the user requested preparation and a Claude prompt while Lightning is unavailable.
  This authorizes planning. C1 approval/acceptance do not authorize C2 implementation.
- Q1–Q5 below are recommendations, not owner decisions. Approve this revision/hash and those
  choices explicitly before code. Preserve C1 approvals and approved plan byte-for-byte.
- BE2-01 stays WAITING_STUDIO, CR01 open, B-12 HANDOFF, OwnerFence ASSUMED_CONTRACT.
  Its pending A17-fix01 verification/review has priority when the named Studio becomes usable.

## 1. Outcome and source coverage

Build a typed context from trusted fixture ports for an authorized source-bound Vision request,
minimize its provider payload, bind output to context/request, and prevent changed or revoked
context from becoming authoritative. Preserve image_only behavior and correction history.

Read `docs/context/SOURCE_REGISTER.md`, this feature's `evidence/notes/SOURCE_AUDIT.md`, C1
approved plan/acceptance, `evidence/notes/H_AI_REVIEW_HANDOFF.md`, and the current source.
Canonical sources: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` and
`features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`.
Pins at the baseline:

| Source | Obligation / C2 treatment |
|---|---|
| SRS FR022/023, lines398–399 | Snapshot, topic, age, request, actions and Teacher feedback; uncertainty and attributable correction. C2 covers an offline subset, not full FR022. |
| UC-018, lines1265–1274 | Versioned source/context, request/action summary by policy, Child statement and Teacher feedback; original observation remains separate from confirmed meaning. |
| SRS schema preamble, lines1577–1579 | Logical contracts and age-policy refinement remain proposed. Only owner-confirmed eligibility36–155 completed months is established. |
| SRS DATA-20/21/22 and CMD-34 | Consent evidence is distinct; source/request/result/correction bindings are distinct. Historical receipt replay requires current disclosure authority. |
| FEAT-040 BE2-02, lines522–532; handoffs128–137 | Versioned candidate contracts, observation/correction provenance, runtime and owner-adapter gates. |
| FEAT-040 BE1 age/consent, lines397–409; BE2-03, lines539–543 | Per-purpose consent, no arbitrary transfer of consent evidence; lifecycle/cancel/budget stay with BE2-03. |

Recommended coverage: source/render/admission + Teacher-authored topic + anonymous per-member
age bands + bounded request enums. Child text, Teacher feedback/confirmed meaning and action
summaries are DEFERRED provider inputs and remain full-card obligations. C1 correction storage
and authority remain. Offline PASS proves contract/adapter behavior, not real model understanding,
quality, deployed serving support, or production privacy/adoption.

## 2. Dependency inventory at98876fe

| Owner / seam | Existing fact | Missing dependency / C2 treatment |
|---|---|---|
| BE1 profiles | `ManagedChildProfile.age_months`, SQL CHECK36–155 | No age-context revision or adopted provider-band policy; fixture owner facts/injected synthetic policy only. |
| BE1 sessions | Free-form configuration JSON; membership/group/turn | No typed topic provenance/exact request-audience snapshot; JSON is not authoritative context. |
| BE1 consent | Child + purpose + state | No versioned provider-transfer/field-use decision; positive fixture permission is not live consent proof. |
| BE1 context | Session aggregate revision exists | No context_revision source; do not substitute session revision. Explicit fixture revision + digest. |
| BE1 canvas | JSON checkpoint/checksum and media artifacts | No verified checkpoint-to-render/admission flow here; preserve C1 fixture bindings and distinct hashes. |
| BE2-01 | RequestRef/JobScope and read-only lineage adapter | No context digest; do not add fields or write job state. Studio verification pending. |
| BE2-03 | No implemented request-owner adapter | AssistancePin and source-only input_hash convention remain ASSUMED_CONTRACT; no lifecycle/cancel/budget implementation. |
| C1 application | AnalysisContextPort, ObservationContext, UoW, applicability | Minimal fake typed mode is not the new provider contract; add a versioned context seam without weakening C1 checks. |
| Lightning V2 | `/v2/vision`, strict request/result with extra=forbid | New envelope cannot be inserted into V2. New client contract/offline transport only; server endpoint does not yet exist. |

## 3. Proposed decisions for owner approval

| ID | Recommended choice | Limit / alternatives |
|---|---|---|
| Q1 | Sorted per-member age-band labels, preserving duplicate bands/count, without member IDs. Exact months remain internal. | Inject `fixture-completed-years-v1`: ten intervals36–47,48–59,...,144–155. FIXTURE_ONLY / NOT_PEDAGOGICALLY_ADOPTED; test coverage/boundaries/overlap/gaps. Alternatives: no provider ages or exact months; neither is selected here. |
| Q2 | Exclude Child-authored intent/explanation/free text. Allow bounded Teacher-authored topic and trusted request reason/target kind/requested-level enums only. | No narration_context substitute or caller authority. Source-undefined enum details are candidate technical decisions documented before code. |
| Q3 | Defer Teacher feedback, confirmed meaning and action summaries as provider inputs in C2. | Keep correction/history locally; retain FR022/UC-018 gaps for a later approved increment. |
| Q4 | New client contract + offline-only injected transport; candidate path `/v1/vision/context`. | Not a deployed API. No server route/prompt change, real HTTP call, retry or image_only fallback. |
| Q5 | Trusted fixture context revision + internal digest, coherent scope binding and pre/post checks. | Real owner context/revision/transfer-policy adapters stay in BE1/BE2-03 handoff. Missing/disagreeing facts refuse. |

Approving these recommendations selects Q1–Q5 for this synthetic component only. It does not
adopt a pedagogical policy, real transfer permission, serving API or owner sign-off.

## 4. Internal context and minimized provider boundary

### 4.1 Trusted internal snapshot

Add a narrow versioned VisionContextSourcePort accepting the trusted AssistancePin and resolved
source. Return one immutable coherent snapshot with exact organization/class/session/canvas/
group/contributor/audience/purpose, assistance identity/request revision, source/checkpoint/render
binding, context revision, per-member completed months/provenance, purpose/consent/provider-transfer
and field-use decisions/revisions, Teacher topic provenance/revision and author role, allowed
request enums, band-policy ref/version and canonical rules version.

Compare against the pin/job/source and existing AnalysisContextPort. Reject missing/extra/duplicate
audience facts BEFORE dict/set conversion; reject scope/source/request/revision or policy mismatch,
and disagreement between eligibility snapshots. Every member must be checked individually BEFORE
removing identity. One unknown/out-of-range age or absent permission refuses the entire call.
No inferred age, topic, consent or revision. This is ASSUMED_CONTRACT, not a real owner-fence proof.

### 4.2 Provider projection

Build strict VisionTypedContextV1 from permitted fields only: contract/version, context revision,
bounded Teacher topic, anonymous per-member band labels/policy version, allowed request enums and
binding hashes. Use an allowlist serializer, never an internal snapshot dump. Exclude DOB/exact
months, member/profile/actor/device/grant IDs, internal consent record/evidence refs, raw scope/
provenance records, Child text, feedback and action history. Existing image transport still needs
its minimum artifact/correlation binding; preserve required image/result identity checks.

Required projected fields lacking permission refuse; no partial payload or fallback. Excluded
optional fields are absent by contract, not accepted then silently dropped. Hashes bind facts/bytes;
they do not prove anonymity, authorization, moderation or permission to transfer real data.

### 4.3 Canonical digests and atomic pinning

- payload_digest: SHA256 of the canonical permitted provider-context projection, excluding digest
  fields and execution time; independently recomputable from that projection.
- context_digest: SHA256 of canonical INTERNAL scope/request/source binding, context revision,
  exact sorted audience facts, provenance and permission decisions/revisions, policy/rules versions,
  and payload_digest. Internal identities remain internal; this digest is opaque to the provider.
  Exclude self-hashes, execution/observation timestamps and correlation IDs.

Use existing foundation canonical JSON/NFC behavior, sorted keys and deterministic arrays. Reject
duplicates, bool-as-int, invalid/empty/newline refs, controls and non-finite numbers before hashing;
never coerce malformed facts. Specify null/absent/empty semantics in the schema and test them.
Exact-month movement INSIDE one band changes context_digest. Policy/permission/request/source
movement must affect it. Do not alter BE2-01 or C1 source-only input_hash.

Store an immutable typed binding (digests + contract/rules versions) reachable from the head/read
path, with an evidence copy/reference. Binding, full provider response, observation and head commit
atomically through the existing fake UoW. Output-evidence fields alone do not update applicability.

## 5. Provider and wire contracts

- Static reviewed capability specifies contract/version, fields and offline transport kind.
  Missing/unsupported capability returns CONTEXT_MODE_UNSUPPORTED before artifact load or calls;
  no automatic downgrade. Real HTTP transport remains unsupported in C2.
- New LightningVisionContextRequestV1 wraps necessary image request and minimized context with
  both digests. New strict LightningVisionContextResultV1 echoes contract/context revision/digests
  and request/source correlation, wrapping an unchanged V2 result. Validate BOTH layers.
- Retain identity/catalog/config/model provenance, admission/source, strict raw confidence, bounds
  and all C1 result checks. Wrong/missing echo is OUTPUT_MALFORMED and stores nothing. An echo
  binds the request; it does not prove the model used context.
- Hash/retain the WHOLE new response document, not just the nested V2 result. One offline call,
  no retries/weights/live inference/prompt change. Reuse small pure verification helpers if needed.
- Add truthful offline_context_adapter evidence; never label typed output offline_legacy_bridge
  or live inference. Existing legacy evidence remains image_only.
- Preserve strict image_only0.1-candidate DTOs and golden bytes. Add sibling typed provenance,
  worker-candidate and internal/Teacher record contracts0.2-candidate, reusing unchanged submodels.
  Do not widen strict old literals silently or subclass with incompatible overrides. CMD-34
  command/receipts and Child projection remain0.1, with no private typed context.

## 6. Processing, staleness and authority

1. Resolve trusted request/job/source/admission and all C1 eligibility checks. Compare the coherent
   typed snapshot, construct permitted projection and pin digests before invoking the provider.
2. Invoke the offline-capable adapter once; validate the full output before staging writes.
3. Re-read current owner facts after the call, including per-member transfer/field permissions and
   eligibility. Revoked consent/purpose/transfer/grant, inactive session or invalid/missing member
   facts reject/discard: no head/observation/provider-result/binding writes.
4. Otherwise context revision OR digest movement makes the validated original stale/non-authoritative
   under C1 semantics. Source movement stays stale; lineage/cancel movement keeps C1 rejection.
   Never silently rebind output to new context. Record the original binding, not current facts.
5. Observation replay, current analysis/read applicability and downstream meaning compare current
   typed binding plus existing disclosure/source/eligibility checks. Same-revision digest movement
   cannot bypass this. No new observation/provider call on replay.
6. NEW corrections against moved typed context fail STALE_CONTEXT before mutation. Previously
   accepted CMD-34 receipt replay remains the immutable historical response after current disclosure
   checks; replay does not revive old meaning. Revoked disclosure blocks it. Preserve existing
   idempotency/If-Match/CAS/rollback behavior.

## 7. Implementation batches and expected files

Paths below are relative to backend/src/sketch2life/; all changes stay in this feature worktree.

| Batch | Deliverable / allowed area | Exit |
|---|---|---|
| C2.1 | New domain/vision_context.py; snapshot/projection/binding rules; narrow application/ports/vision_analysis.py additions | Coherent binding, per-member checks, bounds and deterministic digest tests. |
| C2.2 | New contracts/schemas/vision_context.py and analysis_context_results.py; additive domain binding/evidence kind | New strict wire contracts; old image_only bytes/goldens preserved. |
| C2.3 | application/services/vision_analysis.py; narrow domain/head/UoW/fakes/harness changes | Atomic binding and current checks across observation/replay/new correction/downstream. |
| C2.4 | New infrastructure/vision_analysis/context_adapter.py; small helper extraction from legacy_v2.py if justified | Exact minimized offline transport; full wrapper retention; no V2 behavior change. |
| C2.5 | Unit/contract tests, one typed golden example, concise evidence and handoff | Acceptance map/regression/validators; Codex review-ready; stop. |

Tests belong in backend/tests/unit/ and backend/tests/contract/; examples in this feature's
fixtures/h_ai_review/. No generic context/queue framework or duplicated legacy validator.
Domain/application remain independent of Pydantic/HTTP/storage/provider implementations.

Compatibility exception: the old draft promised all C1 tests unchanged, but
backend/tests/unit/test_vision_analysis_service.py::test_v15_provider_never_receives_age_or_child_content
asserts exact internal dataclass fields for the old fake typed mode. Preserve it if that seam is
unchanged; otherwise explain its narrow supersession, preserve image_only privacy assertions and
add stronger checks on ACTUAL serialized provider bytes. Never remove a guard to get green tests.
Existing image_only goldens need no regeneration.

## 8. Acceptance and negative cases

| ID | Required offline evidence |
|---|---|
| C2-A01 | Strict domain/DTO agreement, versions, bounds/provenance; reject extras, bool/string ages, bad/empty/newline refs and coercion bypasses. |
| C2-A02 | Only trusted scoped facts; caller context cannot become authority. Wrong org/session/canvas/source/purpose/request, missing/extra/duplicate audience and conflicting old/new context ports refuse before invocation. |
| C2-A03 | Every member36–155 and individually eligible; missing consent/transfer/field permission refuses. Synthetic band boundary/coverage tests; no mean/aggregate, member IDs or exact ages in provider context. |
| C2-A04 | Field-use allowlist/revisions; required denied field refuses, excluded fields absent. Internal consent/provenance/member facts do not leak into transport, Child output or logs. |
| C2-A05 | Exact new endpoint/body once via injected transport; no narration_context or Child/feedback/action text. V2 endpoint/payload/behavior unchanged. |
| C2-A06 | Missing/unsupported contract/version/field/transport refuses with zero image loads/calls; no fallback. Real serving NOT_RUN. |
| C2-A07 | Strict wrapper echoes and nested V2 checks; wrong/missing hash/revision/identity rejects. Whole retained response hash equals evidence. |
| C2-A08 | In-flight revision OR digest movement yields stale; same-band exact-age drift with unchanged revision covered. Revocation/ineligibility rejects with no writes; source/lineage behavior preserves C1. |
| C2-A09 | Post-acceptance drift blocks current observation/downstream authority and NEW corrections; authorized historical receipt replay unchanged; revoked disclosure blocks replay. |
| C2-A10 | All C1 guarantees/regressions, raw-result retention, strict bounds/confidence, original/correction separation, Child privacy. Changed seam tests explained, not weakened. |
| C2-A11 | BE1/BE2-03/consumer handoff lists candidate contracts and deferred FR022/runtime coverage; B-12/ASSUMED_CONTRACT labels unchanged. |
| C2-A12 | Canonicalization stable under map/member reorder; duplicates rejected first; source/request/policy/permission/exact-age changes affect internal digest. No self/time fields; payload_digest covers permitted projection only. |
| C2-A13 | Failed commit/CAS/validation leaves no partial binding/head/observation/result. Sequential replay of a stored attempt makes zero new calls. Concurrent first submissions retain one atomic winner and discard the losing result; each submission calls at most once, with no global exactly-once/single-flight claim. |
| C2-A14 | Image_only0.1 DTOs/goldens retain bytes; typed0.2 DTOs accept new records and old strict DTOs reject them. Truthful offline evidence; no invented live/model/owner adoption. |

## 9. Verification, records and stop

Use the existing Python3.12 venv and verify imports point to THIS worktree's backend/src. Isolate
feature-local temp/JUnit/logs; no installs/shared-venv edits. Existing ignored multipart deps/base
Pillow may be loaded process-locally if present, as documented in C1_FINAL_VERIFICATION_20261016.md.
Missing checks stay NOT_RUN, not PASS. The old C1 local wrapper pins old HEAD/source hashes: do
not rerun blindly or overwrite its historical receipts after C2; prepare a new local C2 wrapper.

Run focused C2+C1, relevant legacy Vision/V2/Qwen and BE2-01 non-service regressions, focused
ruff/strict mypy, harness/security/architecture/skeleton and git diff --check. Map C2-A01–A14 to
actual test IDs/outcomes; report collect/pass/fail/skip separately. Prior C1 counts are historical,
not fresh C2 results. No Studio/cloud package or service setup is needed for this offline checkpoint.

After genuine approval, preserve an exact approved plan snapshot/hash. Record the actual owner
message in approvals/C2_TASK_APPROVAL.md, linked from current CONTEXT/status; keep the original
C1 TASK_APPROVAL.md unchanged. Record Q1–Q5 as selected only if the owner selected them. Keep evidence to
one C2 note + one metrics file and update CONTEXT/DECISIONS/STATUS, evidence index, handoff and
current tracker routing. Prompts/raw logs/JUnit/scratch remain under ignored evidence/local/;
no operator prompts or absolute machine paths in published evidence.

Stop at C2_CODE_COMPLETE_PENDING_CODEX_REVIEW. No automatic owner acceptance, full-card DONE,
commit/push/merge/deploy, service provisioning, Studio run or next implementation increment.
Real provider/server/prompt/model/license/quality, owner adapters/fence, persistence/SQL, queues/
lifecycle/budget and live composition remain later gates. If the user redirects to a recovered
Studio, checkpoint this work and follow the saved BE2-01 A17-fix01 procedure.
