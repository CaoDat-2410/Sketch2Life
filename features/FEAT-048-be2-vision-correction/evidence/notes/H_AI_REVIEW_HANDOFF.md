# H-AI-REVIEW consumer handoff — BE2-02 C1 (0.1-candidate)

Producer: BE2-02 C1_COMPONENT_OFFLINE (component candidate, not adopted). Consumers named by
FEAT-040: BE2-03/04/05/06, FE-06/14, BE1-11/12/14, P1 projections, P4 provider wiring.
Everything below is proven only with synthetic fakes; owner adapters are ASSUMED_CONTRACT.

## What a consumer gets

| Artifact | Contract | Example |
|---|---|---|
| DATA-22 worker candidate (exact source field set) | `AnalysisWorkerCandidateV1` | fixtures/h_ai_review/analysis_worker_candidate.json |
| Original observation + bindings + correction history | `AnalysisRecordV1` (Teacher/internal) | fixtures/h_ai_review/analysis_record.json |
| CMD-34 Teacher receipt | `AnalysisCorrectionEnvelopeV1` / `AnalysisCorrectionReceiptV1` | fixtures/h_ai_review/correction_teacher_receipt.json |
| CMD-34 Child-device receipt (refs/status only) | `AnalysisCorrectionChildEnvelopeV1` | fixtures/h_ai_review/correction_child_receipt.json |
| Versioned invalidation intents | `InvalidationIntent` (domain, committed with each mutation) | fixtures/h_ai_review/invalidation_intents.json |
| Downstream meaning | `VisionAnalysisService.downstream_meaning` → `DownstreamMeaning` | fixtures/h_ai_review/downstream_meaning.json |
| Full original provider result (Teacher/internal only) | `VisionAnalysisService.resolve_provider_result` → `ProviderResultRecord` | fixtures/h_ai_review/provider_result_record.json |

Examples are deterministic (`infrastructure/vision_analysis/harness.build_handoff_examples`, offline
legacy bridge over a scripted transport) and pinned by `tests/contract/test_h_ai_review_handoff_examples.py`.
The foundation's shallow DATA-22 `ShapeSpec` is unchanged and still accepts the strict candidate.

## Semantics consumers must keep

- **Refs.** `analysis_id` + `analysis_revision` (ETag `"analysis:<id>:<rev>"`, strong comparison)
  identify the aggregate. `observation_sha256` identifies the immutable original; corrections are
  `correction_id` + `correction_version` (= analysis revision they created).
- **Five distinct hashes.** `evidence_refs` kinds `vision_observation`, `provider_result`,
  `source_checkpoint` (JSON checkpoint checksum), `source_render` (PNG/JPEG bytes) and
  `admission_receipt`. Never substitute one for another; the contract rejects checkpoint = render.
  The `provider_result` ref (`result:<analysis_id>`) resolves through the trusted resolver to the
  retained canonical JSON of the whole typed result; its SHA256 equals the emitted hash and it
  rebuilds the original `VisionUnderstandingSuccessV2` (incl. correlation id). Never shown to Child.
- **Bounds.** Observation refs ≤120 chars matching `^[a-z0-9-]+$`; object candidates, unknown-
  confidence refs and ambiguous regions ≤256 each. Provider output beyond these is
  `OUTPUT_MALFORMED` before storage, never truncated. Correction history is projected complete.
- **Observation replay.** Re-running a worker claim for an existing (job, attempt) never calls the
  provider again; its `authoritative` flag reflects the current gate/context/source, so a stale or
  revoked analysis replays as `stale`/`rejected`, not as current authority.
- **Job scope.** BE2-01 job session, subjects (= audience), purpose and target (= assistance id)
  must match the assistance pin (`JOB_SCOPE_MISMATCH` otherwise).
- **Uncertainty.** `confidence` is `null` when uncalibrated — not 0, not certainty. Calibration is
  always `uncalibrated` in C1; `unknown_confidence_refs` lists every null-confidence observation;
  `requires_meaning_confirmation` is always true. Top label is never ground truth.
- **Meaning.** `child_proposal` (bound Child device, current open turn, own participant) is always
  `proposed` and never effective. Only a scoped Teacher's `teacher_confirmation` becomes
  `current_meaning_ref`. Use confirmed concepts **only** when `downstream_meaning.state ==
  "confirmed"`; `unconfirmed` means use nothing as the child's intent; `not_applicable` means the
  analysis is stale (context/source changed, owner invalidation, consent) — request a new one.
  `meaning_kind=intended_concept`: an imagined concept, not a verified fact.
- **Not a review.** A confirmation is not a DATA-24 review and approves no Sketch, session,
  proposal or other analysis. BE2-04/05 must still run their own review gates.
- **Source revisions.** Records pin `input_snapshot_ref`, checkpoint id/epoch/revision/checksum,
  render ref/hash, admission receipt id, `context_revision`, assistance id/request revision and
  job id/attempt id. A stale analysis keeps every pin and its history.
- **Invalidation.** Each correction writes `child_intent_proposed` or `teacher_meaning_confirmed`;
  owner notices write `source_changed`/`context_changed`/`intent_changed`/`consent_revoked`, with
  deterministic `event_id`, previous/new revision and correction ref. Consumers dedupe by
  `event_id`. Delivery transport is NOT_RUN (no event platform in C1).
- **Provider context.** `provider_context_mode=image_only` for the legacy bridge: topic, age,
  Child intent and Teacher feedback were **not** given to the model. Do not describe results as
  context-aware inference.
- **P1 projection.** The Child-device projection carries only analysis/correction refs, kind,
  `meaning_status` and time — no labels, confidence, uncertainty, provenance, moderation,
  Teacher text or age. Unsafe/malformed provider output is never stored. Age-appropriate wording
  of any Child-facing text remains a P1/BE2-05/06 responsibility.
- **P4 wiring.** The bridge refuses the real `UrllibJsonTransport`; credentials and endpoints stay
  backend-only and need a separate approval to inject.

## Missing before BE2-02 can close (not provided by C1)

1. Additive typed provider-context protocol (topic/age-policy/context revision) and a provider
   that consumes it; until then typed mode fails closed (`CONTEXT_MODE_UNSUPPORTED`).
2. Model/profile/serving/license/budget adoption and measured quality on the new context
   (real inference report with model revision/profile/input hash).
3. Real BE1 adapters: snapshot/checkpoint/render source, media-admission receipt, Teacher grant
   and device turn binding, consent/purpose/age/context revision (H-CANVAS-SYNC, H-CLASS-CONSENT).
4. BE2-03 assistance request lifecycle and the agreed request `input_hash` formula (C1 candidate:
   canonical hash of snapshot ref + checkpoint identity/checksum + render ref/hash).
5. BE2-01 lineage over the SQL repository at runtime (adapter uses the port; only the fake was run).
6. Durable persistence (tables/migrations for heads, observations, retained provider results,
   corrections, receipts, invalidation intents, notices), owner fences, outbox delivery, history
   paging and their runtime evidence.
7. Live API composition, real authentication, P4 provider wiring, independent review/sign-off.
8. Legacy F-01 decision (V2 adapter `OSError` branch) by the legacy owner.

## Verification update —2026-10-16

All six C1 findings closed; focused233 tests and V2 server7 tests now pass with
0 skips, plus the separate foundation live-route check1/1. Evidence:
C1_FINAL_VERIFICATION_20261016.md and the corresponding metrics under ../metrics/.
This replaces earlier missing-dependency statuses only; all full-card gates and
synthetic/ASSUMED_CONTRACT consumer limitations above remain. Owner acceptance
and production/runtime integration are not implied by passing local checks.

## C2 typed-context candidate —2026-10-17

Current status (2026-10-17 11:59 +07:00): Codex CODE_REVIEW_PASS_WITH_NOTES
(C2_CODEX_REVIEW_20261017.md) and owner ACCEPTED as an offline component
(../../approvals/C2_COMPONENT_ACCEPTANCE.md). This section was first written at
C2_CODE_COMPLETE_PENDING_CODEX_REVIEW; the acceptance does not mean full BE2-02, production
adoption, BE1/P1/P4 sign-off or real provider/model/runtime evidence, and the review's notes stay
open. Everything is synthetic and ASSUMED_CONTRACT; B-12 HANDOFF and OwnerFence ASSUMED_CONTRACT
labels are unchanged.

| Artifact | Contract | Example |
|---|---|---|
| Provider typed context (client, not deployed) | `VisionTypedContextV1` 0.1-candidate | typed_context_example.json `provider_context_request.typed_context` |
| Context request/response wrapper, path `/v1/vision/context` | `LightningVisionContextRequestV1` / `LightningVisionContextResultV1` 0.1-candidate | same file (image bytes elided) |
| Typed worker candidate / record / binding | `AnalysisWorkerCandidateV2`, `AnalysisRecordV2`, `TypedContextBindingV2`, `TypedProvenanceV2` 0.2-candidate | same file `analysis_record` |
| Retained whole wrapper | `ProviderResultRecord` (`result_contract` `LightningVisionContextResultV1/0.1-candidate`) | same file `provider_result_record` |

Example: ../../fixtures/h_ai_review/typed_context_example.json, pinned by
`tests/contract/test_vision_context_contracts.py`. image_only 0.1 examples above are unchanged.

Consumer semantics:

- `provider_context_mode=typed_context` + `evidence_kind=offline_context_adapter` means an
  injected offline transport echoed the pinned binding. It does NOT mean a model used the context.
- The provider sees only: Teacher topic (or null), one anonymous age-band label per audience
  member (FIXTURE_ONLY policy `fixture-completed-years-v1`, not pedagogically adopted), request
  enums and the source image hash. No ids, exact months, consent records, Child text, Teacher
  feedback, confirmed meaning or action summaries.
- `payload_digest` binds that projection; `context_digest` is an opaque internal binding of scope,
  source, request, exact owner facts and permission/policy revisions. Same-revision exact-age or
  permission movement makes an analysis `stale`/not applicable; consumers must not rebind.
- Current transfer/field-use/consent/eligibility refusal discards an in-flight result and makes a
  stored one non-authoritative; accepted CMD-34 receipts still replay as history after the current
  disclosure check (consent revoke blocks it; transfer revoke does not). Replay never revives
  meaning. CMD-34 receipts and the Child projection stay 0.1 and carry no typed context.
- Old strict 0.1 DTOs reject typed records; consumers that cannot read 0.2 must refuse them.

Still missing before BE2-02 can close (in addition to items 2–8 above): a real provider/server
consuming the context and evidence that it is used; an adopted band policy; BE1/BE2-03 adapters
for context revision, transfer and field-use permission, topic provenance and request enums;
FR022/UC-018 deferred inputs (Child statement, Teacher feedback/confirmed meaning, actions).
Evidence: C2_IMPLEMENTATION_EVIDENCE_20261017.md and ../metrics/C2_IMPLEMENTATION_CHECKS_20261017.json;
review C2_CODEX_REVIEW_20261017.md; acceptance ../../approvals/C2_COMPONENT_ACCEPTANCE.md.
