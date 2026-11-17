# BE2-02 — source-bound Vision and attributable correction

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Checkpoint: C1_COMPONENT_OFFLINE; not full-card DONE
- Source: Master SRS v3.1; FEAT-040 BE2-02; FEAT-044 roadmap/current checkpoint.
- Branch/base: feature/be2-02-vision-correction /6dcc57ee0b3d053f071c8c92e72aaaee2e98d899.
- Executor after actual approval: Claude; planning/code review: Codex.

## 1. Goal and source obligations

Given an authorized pinned canvas render/context and verified job lineage, record Vision
candidates/uncertainty with original provenance; preserve that observation when Child intent
or Teacher correction differs. Only current scoped authority can make a new correction effective.

FR022/023/061 are CONFIRMED. UC-018 detail/DATA-22/CMD-34 are proposed logical design;
DECISIONS D01–D11 are candidate interpretations for explicit component approval, not production
adoption. No source obligation is removed by this smaller C1 checkpoint.

Card outputs: Vision port/adapter mapping; snapshot/version/hash validation; DATA-22 persistence
port; CMD-34 use case/handler; wrong-recognition/low-confidence/malformed fixtures; H-AI-REVIEW
source/correction refs, uncertainty, source revisions and invalidation handoff.

## 2. Scope now and remaining work

**C1:** strict additive DTOs; pure domain/application; narrow external ports; in-memory transactional
repository/authority/context/admission/job-lineage fakes; additive offline bridge around the
existing V2 adapter/transport; isolated CMD-34 fixture API; focused synthetic tests and handoff.

**Excluded:** real model/provider/network; weights/GPU/ASR/microphone/camera; dependency install;
SQL migrations/DB adapter or Redis/RQ changes; production auth/router/P4 wiring; changes to BE1,
FEAT-018, foundation01 or other cards; SAM/rigging/Sketch generation; model tuning; Git publication.

Remaining full-card gates: real typed topic/age/intent/context consumption; model/profile/serving/
license/budget adoption and measured quality; real owner/admission adapters; persistence/runtime
strategy/evidence and live composition. C1 alone cannot close BE2-02.

## 3. Behavior and authority

1. Resolve current scope, source/checkpoint/render/admission and request/job identity through
   trusted ports. A caller-supplied org/actor/participant is not authority. Opaque snapshot ref
   resolves to exact source metadata/bytes; record request/context/job revisions distinctly.
2. Authorize before provider invocation/disclosure. Age is authoritative36–155 completed months,
   not model inference or the legacy under-nine helper. Recheck eligibility before acceptance.
3. Keep the whole original typed observation/ref/hash immutable. Source/context/intent/revoke/
   cancel change makes old results non-applicable, never silently rebound to new source/meaning.
4. Bound Child may submit own intent/correction proposal; current scoped Teacher confirms
   authoritative meaning. Document candidate proposal/confirmation states before code. A device
   cannot become Teacher by request payload. Correction does not authorize a Sketch or session.
5. New CMD-34 mutation requires idempotency key and analysis-family If-Match. After current
   permission-to-disclose check, identical accepted replay returns original receipt even with
   old If-Match; changed payload conflicts. Unseen mutation checks current purpose/scope/context
   and CAS. Revoked actors cannot retrieve private accepted receipts.
6. Component UoW atomically commits mutation, receipt and invalidation intent. Losing CAS and
   injected failures leave no partial mutation. Real DB/owner fence/delivery proof remains
   NOT_RUN/ASSUMED_CONTRACT; do not implement another foundation or generic queue platform.
7. Child projection uses safe refs/status, not raw prompts/confidence/unsafe/pending content.
   Full moderation/review/Child delivery remains05/06; imagined details never become factual
   verification, and no age/psychology/IQ inference is introduced.

## 4. DATA-22 field rationale

Use source-based names and define concrete candidate types in DECISIONS before implementation.
Keep input_snapshot_ref an opaque reference compatible with the foundation shape where possible;
rich trusted context is resolved server-side. Do not rewrite the shallow ShapeSpec as if frozen.

| Field/group | Source / producer | Invariant / consumer |
|---|---|---|
| assistance_id, expected_request_revision | DATA-22; trusted request port/fixture | Consume BE2-03 identity, do not implement its lifecycle |
| input_snapshot_ref, context_revision | DATA-22/DATA-20/B22.3 | Exact source/scope binding and current eligibility |
| job_id, job_attempt_id | DATA-22/DATA-25 | Verified internal lineage, not arbitrary public completion |
| contract_version | DATA-22 | Explicit0.1-candidate, no registry/production sign-off |
| object_candidates(label,confidence) | DATA-22 from V2 entities | Null or finite strict number[0,1]; reject bool/string/NaN, never synthesize score |
| uncertainty | DATA-22; provider/mapping | Candidate structure documented; null confidence is not zero or certainty |
| evidence_refs, provenance | DATA-22/UC-018 | Full original typed result/ref/hash, source/profile/model and fixture/live evidence kind |
| moderation_outcome | DATA-22/FR061 | Candidate outcome/policy provenance; lexical pass is not overall clearance |
| analysis_id, analysis_revision, accepted_status | DATA-22; application | Server-derived; documented candidate disposition, not new job state |
| intended_objects, child_explanation, correction_reason, expected_context_revision | DATA-22 correction | Strict text bounds with rationale; reason/context required; child_explanation nullable, omitted-vs-null semantics documented as a C1.1 candidate choice |
| correction ref/version/author/meaning status | DATA-22 response/UC-018 | Immutable attributable history; Child proposal distinct from Teacher confirmation |
| org/session/canvas/contributor/audience/consent/turn refs | DATA-20/21 + owner handoffs | Server-resolved, never proof merely because client supplied it |
| checkpoint id/epoch/revision/checksum | DATA-20/CanvasCheckpointMetadata | JSON checksum distinct from render SHA256 |
| rendered artifact/hash, derivation/admission receipt | DATA-20/media contracts | Admission binds exact render; never manufacture PASS |
| command fingerprint/receipt/invalidation event id | Common CMD rules; technical | Actor/org/contract/target/key scope, replay/CAS/rollback, no generic event platform |
| provider_context_mode/execution evidence | Technical truthfulness | image_only/fixture explicit; no claim of typed provider context or live inference |

Every added field must have source/technical rationale, producer/consumer, constraint and test.
Do not add fields for unspecified future use, arbitrary production numeric policy or credentials.

## 5. Existing adapter reuse and concrete gaps

Reuse VisionUnderstandingPortV2 and LightningVisionV2Adapter through injected JsonTransport,
artifact_loader and clock. Add a narrow new bridge; preserve V1/V2 DTOs, Qwen runner, production
app and legacy behavior. No SDK/install is needed for offline mapping.

V2 has no typed topic/age/context fields. Its optional narration hint is adult-authored.
**Do not hide Child intent/topic/age/actor in narration_context and claim typed support.**
C1 fake provider accepts the new envelope; legacy bridge labels image_only and retains app-side
context binding. Real full-context activation must fail closed until an additive payload/handler
decision supplies the missing capability. No real provider is called under C1.

Bridge checks correlation/image/profile/catalog/config/model provenance and retains all original
entities/actions/relations/themes/ambiguous regions and evidence. Map entity label.value and null
confidence only where semantically valid. Malformed/unsafe result becomes a typed safe outcome;
legacy lexical PASSED is not comprehensive moderation. No automatic transport retry.

First bridge uses source-only admitted PNG/JPEG. Reject processing-image refs the transport
would ignore. A supplied legacy media PASS is insufficient: trusted admission receipt must bind
the exact render hash. JSON checkpoint checksum does not prove media admission.

Old Gate-A/semantic principals/child_age helpers are not Teacher/Child authority. AiJob actions
are create/read/cancel only. Use correction-specific candidate authority/context/admission/lineage
ports and fakes; no direct BE1 DB reads. A unit fake proves the proposed protocol only.

## 6. Five batches and expected modules

Paths are proposed narrow modules; equivalent existing conventions are allowed with mapping
recorded before code. Domain imports no Pydantic/contracts/infrastructure/framework/provider.

| Batch | Deliverable / expected files | Exit |
|---|---|---|
| C1.1 | domain/vision_analysis.py; contracts/schemas/analysis_results.py; concrete candidate decisions | Immutable observation/correction, strict DATA-22 and field/source map |
| C1.2 | application/ports/vision_analysis.py; application/services/vision_analysis.py; infrastructure/vision_analysis fakes | Authority/source/lineage, Teacher/Child, receipts/CAS/rollback/invalidation |
| C1.3 | infrastructure/vision_analysis/legacy_v2.py | Offline reused transport, identity/provenance/admission checks and context gap label |
| C1.4 | CMD-34 handler/router under interfaces/http/routers plus isolated feature fixture composition | Preconditions/idempotency/errors/role-safe projections; no production app mount |
| C1.5 | Focused unit/contract/fixture API tests, evidence and H-AI-REVIEW handoff | V01–V17 mapped to actual results, then stop for Codex review |

No new standalone conformance framework or large runner is required; pytest plus acceptance-to-test
mapping is enough. A tiny fixture entrypoint is optional only if it adds nonduplicated consumer usage.

## 7. Acceptance C1 — component evidence only

| ID | Required behavior / negative cases |
|---|---|
| V01 | Strict valid/invalid DTOs; no caller-controlled server identity/status/author; null confidence preserved; bool/string/nonfinite/out-of-range rejected |
| V02 | Checkpoint epoch/revision/checksum, render hash/provenance and trusted admission independently bound; wrong/missing binding calls no provider and stores no authoritative result |
| V03 | Valid snapshot yields traceable uncertain candidate and complete original observation; low/unknown confidence is not invented intent |
| V04 | Cat observation→Child tiger proposal→Teacher confirmation: cat remains immutable, authors/history distinct; downstream tiger authoritative only after authorized confirmation |
| V05 | Wrong org/class/session/canvas/group/participant, unbound/closed turn, revoked grant/purpose/consent denied; client cannot impersonate Teacher/another child |
| V06 | Snapshot/context/intent changes in-flight: pinned original retained, result non-applicable/stale, newer confirmed meaning not overwritten; AT-CS-008 |
| V07 | Wrong job/attempt/request/input hash, cancelled/superseded completion cannot create authoritative analysis; consume foundation lineage without rewriting it |
| V08 | Same accepted key/payload replays original correction/version/event; changed payload conflicts; org/principal/target scopes isolate keys |
| V09 | Authorized accepted replay with old If-Match returns original receipt; revoked read denies; unseen command missing If-Match428, wrong family/revision412 |
| V10 | Two component writers at one revision: one CAS winner, loser no correction/receipt/event; injected storage failure rolls back staged effects |
| V11 | Correction emits versioned downstream invalidation intent; old result/review not silently authoritative, history preserved, no fabricated Teacher review |
| V12 | Isolated CMD-34 fixture positive/negative cases, safe codes/projections, current authority; production app unchanged |
| V13 | Offline legacy valid/wrong label/null confidence/malformed/timeout/prohibited output; correlation/image/profile/catalog/config/model mismatch fails safely; no automatic retry |
| V14 | Source-only/admission restrictions and explicit image_only context mode; unsupported context not silently supported; no Child content passed as adult narration |
| V15 | Unsafe/pending/raw model content unavailable to Child; no age/mental-state inference; authoritative36–155-month context, not legacy under-nine helper |
| V16 | Field map/decisions/synthetic examples/consumer handoff enumerate missing real owner/provider/persistence/runtime/adoption; no full-card DONE |
| V17 | Existing Lightning/Qwen adapter tests and relevant foundation regressions remain green; required missing dependency/check is NOT_RUN with exact reason |

Use canonical safe errors where applicable: STALE_CONTEXT409, STALE_AGGREGATE412,
PRECONDITION_REQUIRED428, IDEMPOTENCY_PAYLOAD_MISMATCH409, FORBIDDEN_SCOPE/GRANT_REVOKED/
CONSENT_REQUIRED403, validation422, UNSAFE_CONTENT409, DEPENDENCY_UNAVAILABLE503. Candidate
catalogue status remains explicit. Do not leak inaccessible resources, raw provider data or keys.

## 8. Verification and evidence

Use the existing Python3.12 environment and point imports at this worktree. An editable venv
may point at sibling FEAT-018: verify actual module paths before tests. No installs/provider calls.
Run focused domain/service/contract/bridge/fixture API tests with isolated basetemp and JUnit;
existing test_lightning_vision_v2_adapter.py/test_qwen_vision_adapter.py and relevant BE2-01
unit/contract regressions. Run ruff/mypy for changed files, harness/security/architecture/skeleton/
diff checks. Broaden only for a concrete change/risk; do not claim whole-project PASS from a subset.

Record actual command/environment/source+dirty hashes/UTC/input hashes/results/skip reasons and
V01–V17 mapping. Keep raw repeated logs/scratch/personal prompts under ignored evidence/local;
summary under notes/metrics. Preserve failures; no synthetic JUnit as runtime or repeated runs to
select PASS. Fake proof, real runtime and integrated evidence remain distinct.

## 9. Approval and stop

Before code record a real user C1 planrev1 approval with exact text/hash/revision/scope/timestamp
in approvals/TASK_APPROVAL.md, then update current work order. A template is not approval.
Material scope/authority/contract gaps require a narrow decision before dependent work;
routine choices within approved D01–D11 do not require repeated approval. End at review-ready
C1 component evidence; no commit/push/merge/deploy and no full-card closure.
