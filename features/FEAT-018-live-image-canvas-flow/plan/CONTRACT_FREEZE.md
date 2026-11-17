# FEAT-018 shared contract freeze

## Purpose

This document is the single contract source for the four person plans. A person may add an implementation detail only if it preserves these names, versions, required fields, provenance rules, and failure semantics. No person may invent a parallel field name or silently change a version.

## Contract authority and change rule

- Domain/API schemas are authoritative in `backend/src/sketch2life/contracts/schemas/` and their generated JSON Schema artifacts.
- Mobile and renderer types are mirrors generated or manually checked against the same JSON Schema; they are never a second source of truth.
- Fixture manifests declare contract names and versions and are validated before any device run.
- A breaking field change increments the contract major/version name (for example `VisionUnderstandingResultV1` → `VisionUnderstandingResultV2`), updates every producer/consumer, and adds a migration fixture. A compatible optional field increments the minor `contract_version` only after review.
- Every request carries `session_id`, `expected_session_version`, `request_id`, and an idempotency key at the transport boundary. Every result carries `contract_name`, `contract_version`, status, provenance, and a typed failure when failed.
- No raw media, prompt, model output, token, signed URL, or personal metadata enters normal logs/evidence.

## Canonical version registry

| Contract | Version | Owner | Consumers | Required invariants |
|---|---|---|---|---|
| `MobileWorkflowCommandV1` / `MobileWorkflowResultV1` | 1.0 | shared/mobile | backend/mobile | request/idempotency/session/version/actor envelope; every result has status, typed provenance and typed failure on FAILED; `request_id` maps to FEAT-016 `command_id` once |
| `WorkflowResultProvenanceV1` / `WorkflowFailureV1` | 1.0 | shared/mobile | backend/mobile | transport-only provenance/failure wrapper; safe message, stable code, retryability; never leaks raw provider detail |
| `SessionSnapshotV1` | 1.0 | shared/mobile | backend/mobile | state/version, aware created/updated/expiry timestamps, optional typed job, `durable=false`; no owner identity or media bytes |
| `WorkflowJobV1` | 1.0 | backend | backend/mobile | process-local poll state; terminal result/failure is typed; no provider body or media payload |
| `SessionGalleryV1` / `SessionJourneyEntryV1` | 1.0 | shared/mobile | backend/mobile | one-session projection only; metadata/opaque refs, never media bytes, owner identity, or durable-history claims |
| `FeedbackV1` | 1.0 | shared/mobile | backend/mobile | exact activity/objective/template/spec identity; bounded scores and controlled tags; no free-text or child profile fields |
| `SourceMediaReferenceV1` | 1.0 | P2 | P1/P2/P3/P4/backend | `artifact_ref`, `sha256` only when `AVAILABLE`, `source_status`, immutable original; working copy never replaces source |
| `MediaValidationResultV1` | 1.0 | P2 | backend/mobile | `PASS` or `RECAPTURE`, ordered stable reasons, image/audio signals, validator policy version |
| `ModelProvenanceV1` | 1.0 | P2 | all AI evidence | provider, exact model, adapter version, config version; no token/URL |
| `AsrRequestV1` / `AsrResultV1` | 1.0 | P2 | fusion/backend | source audio ref, transcript/segments/quality on success; typed failure on failure |
| `VisionRequestV1` / `VisionUnderstandingResultV1` | 1.0 | P2 | legacy consumers | retained for compatibility; not the FEAT-018 P2-T2 integration contract |
| `VisionUnderstandingRequestV2` / `VisionUnderstandingResultV2` | 2.0 | FEAT-003 | FEAT-018 P2-T2 consume-only adapter | FEAT-003-owned typed V2 union; FEAT-018 may consume through the approved adapter boundary and must not modify the V2 schema/runtime |
| `RawUnderstandingResultV1` | 1.0 | P2 | Gate A/P1 | typed observation groups, confidence `0..1`, required source SHA-256, typed failure, uncertainty/conflicts and `gate_a_required=true`; observations never equal eligibility |
| `GateAConfirmationV1` | 1.0 | shared | backend/mobile/session | Gate-A-only confirmation: session/version, adult actor, meaning version, confirmed claim IDs and optional correction; cannot approve eligibility/safety |
| `IntegrationGateDecisionV1` | 1.0 | shared | mobile/session | Gate-B-only decision: status, session/version, actor at transport boundary, exact activity/objective/template/spec IDs and versions |
| `P1ContextV1` | 1.0 | P1 | P1 filter/backend | explicit age, readiness, completed activities, materials, supervision, policy flags, candidate status |
| `P1FilterResultV1` | 1.0 | P1 | Gate B | status, exact activity/objective IDs and versions, ordered reason codes |
| `PixiArtAssetManifestV1` | 1.0 | P3 | renderer/mobile | immutable source hash + exactly one original asset; supplemental assets require per-asset visual approval and rights clearance; no paths or media bytes |
| `ArtAnimationPlanV1` | 1.0 / renderer protocol 1 | P3/shared | renderer/bridge | ExperienceSpec + source identity wrapper around the unchanged camelCase renderer payload; bounded motions, known targets, source hash continuity, video disabled |
| `RendererBootstrapV1` / `RendererEventV1` | renderer protocol 1 | P3 | mobile/WebView | protocol version, renderer instance ID, discriminated lifecycle events; strict schema and 4096-byte bridge message cap |
| `LearningMediaRequestV1` / `LearningMediaResultV1` | 1.0 | P4 | P3/mobile | exact activity/objective/renderer versions, cache status, generation-called flag, provenance |
| `ActivityHandoffV1` | 1.0 | P1/shared | mobile/offscreen activity | exact activity/objective IDs and versions, source session version, ready status |

## Field-level rules

The 2026-09-18 approved Shared Integration Addendum Rev 2 resolves the Gate-A/Gate-B registry ambiguity: `GateAConfirmationV1` is the versioned meaning-confirmation command; `IntegrationGateDecisionV1` remains the Gate-B result/decision and its implementation's `gate` is `"B"`. The framework-free FEAT-016 `GateAConfirmation`/`GateBDecision` types are internal adapters and must preserve those exact versioned fields. The MobileWorkflow envelopes are transport-only and do not replace domain contracts. `MobileWorkflowCommandV1.request_id` is translated once to the reducer's `command_id`; the idempotency key remains at the HTTP/application boundary.

Required state order for the shared live-image slice is: valid P1 filter → `CANDIDATES_READY`; immutable ExperienceSpec + fit validation → `GATE_B_PENDING`; Gate B approval of the exact spec → `EXPERIENCE_READY`. FEAT-016's fixture reducer and transition tests were reconciled on 2026-09-18; 13 focused tests pass, including rejection of the previous order, retake invalidation, explicit `completed_activity_ids`, and exact Gate-B activity/objective/template/spec identity. P1 context validation includes every field in `P1ContextV1.missing_fields()`, especially explicit `completed_activity_ids`.

### Source and validation

`SourceMediaReferenceV1` keeps the original `artifact_ref` and SHA-256. `source_status=AVAILABLE` requires a 64-character lowercase SHA-256. `MISSING`/`UNREADABLE` cannot carry a hash. A working copy is derived-only and must point back to the original.

`MediaValidationResultV1` preserves image/audio references even when one modality is missing. `decision=RECAPTURE` stops inference. Stable reasons include unreadable, too-small, too-dark, low-contrast, blurry, framing-risk, silent/no-speech, duration, clipping, and unsupported media.

### AI results

Successful ASR/Vision results require available source, no failure object, and complete model/config provenance. Failed results require one typed `AdapterFailureV1` code. The allowed failure codes are `VALIDATION_REJECTED`, `TIMEOUT`, `PROVIDER_ERROR`, `RATE_LIMITED`, `MALFORMED_OUTPUT`, `PROHIBITED_FIELD`, and `SOURCE_MISMATCH`.

`RawUnderstandingResultV1` preserves ASR and Vision separately. `claims[].source` is `ASR`, `VISION`, or `FUSED_PROPOSAL`; `conflicts` and uncertainty are retained. `gate_a_required` is always true for a live proposal. No AI output may contain psychological/personality or eligibility claims.

### Gates and session

Gate A confirmation records `meaning_version`, `confirmed_claim_ids`, actor, expected session version, and optional adult correction. Gate B records exact activity/objective ID+version pairs and rejects stale session versions, inactive records, mismatched objective mappings, and missing hard-rule context.

### P1 context and identity

P1 context is adult-provided. The runtime must not infer `age_months`, readiness, completed activities, available materials, supervision, or policy flags from media. `P1FilterResultV1` is either eligible or blocked and always carries ordered reason codes.

### Renderer and media

`PixiArtAssetManifestV1` references the immutable source and optional derived masks/regions. Exactly one source-original item is mandatory; every supplemental item is fail-closed unless individually visually approved and rights-cleared. `ArtAnimationPlanV1` wraps the unchanged protocol-1 renderer payload and binds it to the session's exact ExperienceSpec and source hash. The source drawing remains present and unmodified. Renderer messages are strict, size-bounded, and allowlisted; no video or generated asset can be invoked. `LearningMediaResultV1` must preserve activity/objective/renderer identity across cache hit, miss, timeout, and fallback.

## End-to-end state sequence

```mermaid
sequenceDiagram
  participant M as Mobile
  participant S as Session API
  participant V as Validator
  participant A as AI backend
  participant G as Gate A
  participant P as P1 catalog
  participant X as Experience compiler
  participant C as P4 cache
  participant R as Pixi renderer
  M->>S: CREATE_SESSION (UUIDv4, version 0, idempotency)
  S-->>M: session snapshot (version 0, ephemeral)
  M->>V: non-child image + session/version
  V-->>M: MediaValidationResultV1
  V->>A: validated image bytes (only after provider gate)
  A-->>M: RawUnderstandingResultV1 + proposal
  M->>G: adult confirmation/correction
  G->>P: confirmed meaning + adult P1ContextV1
  P-->>M: P1FilterResultV1
  P->>X: exact candidate identity
  X-->>M: immutable ExperienceSpecV1 + fit result
  M->>G: Gate B exact activity/objective/template/spec refs
  G->>C: LearningMediaRequestV1
  C-->>M: LearningMediaResultV1 (same identity; fallback allowed)
  M->>R: approved-only Pixi manifest + source-locked plan
  R-->>M: validated renderer events
  M->>S: ActivityHandoffV1 + FeedbackV1
  S-->>M: session-only gallery projection
```

## Cross-person handoff table

| From | To | Input | Output | Blocking condition |
|---|---|---|---|---|
| P2 | P1/Gate A | validation + ASR/Vision | `RawUnderstandingResultV1` | invalid source, malformed/prohibited output, missing provenance |
| P1 | Mobile/P4 | `P1ContextV1` | `P1FilterResultV1` | missing context, hard safety/material failure, stale catalog |
| P1 | Gate B/P4 | candidate identity | `IntegrationGateDecisionV1` | mismatched IDs/versions or Gate A absent |
| P4 | P3 | `LearningMediaResultV1` | approved asset/plan references | cache miss, unsafe/corrupt/stale media |
| P3 | Mobile | `PixiArtAssetManifestV1` + `ArtAnimationPlanV1` | renderer events | invalid plan, source hash mismatch, bridge error |
| Mobile | shared | state + identity | `ActivityHandoffV1`, `FeedbackV1` | any gate/session invariant failure |

## Reconciliation status

1. Resolved 2026-09-12: FEAT-018 P2-T2 consumes FEAT-003's approved `VisionUnderstandingResultV2` through the cross-feature adapter boundary. FEAT-018 owns a separate `RawUnderstandingResultV1` semantic handoff and must not alias FEAT-017's flat V1 or modify FEAT-003 V2. The FEAT-003 cross-feature addendum and FEAT-018 P2-T2 task addendum are recorded in the canonical approval files.
2. Resolved 2026-09-18: the shared FEAT-016 and Android fixture identity now pairs `ACT-0004` v2 with primary `OBJ_OBJECT_PERMANENCE` v1, consistent with the reviewed catalog; no movement-coordination identity is allowed for this activity.
3. `packages/art-renderer` includes a standalone browser runtime/POC. Canonical backend schemas for the approved-only manifest, source-locked plan wrapper and strict bounded protocol-v1 events are tested against the TypeScript mirror. Expo WebView/native lifecycle integration remains for M6.

`SessionSnapshotV1` freezes state/version, aware expiry and optional typed last-job projection. The TTL duration is a runtime setting; session/job/artifact state remains process-local and expires without durable saving. Application interfaces and in-memory adapters provide the future storage seam without an `owner_ref` field.

## Contract-freeze evidence

- JSON Schema export and compatibility report.
- Fixture manifest contract registry check.
- Producer/consumer table for all four people.
- Positive, malformed, stale, missing-context, fallback, and redaction fixtures.
- One review record for every contract version change.

## Revision-2 engine contracts — approved and frozen

The approved FEAT-018 revision-2 engine adds a shared semantic handoff so video metadata, original-art animation and the off-screen activity cannot choose independent concepts. The contracts below are active at version 1.0; the video consumer remains metadata-only for the current demo.

| Proposed contract | Owner | Purpose |
|---|---|---|
| `SemanticAnchorSetV1` | P2 -> P1 | Confirmed subject/action/feature/story observations with source claims and adult correction. |
| `LearningFocusV1` | P1 | One selected anchor and one learning objective for the session. |
| `ActivityTemplateV1` | P1 | Curated activity family, objective compatibility, materials, safety and personalization slots. |
| `ExperienceSpecV1` | P1/shared | Immutable source of truth for video, animation, activity plan and bridge sentence. |
| `ActivityFitEvaluationV1` | P1/shared | Deterministic relevance, objective, continuity and Montessori/safety score. |
| `BridgeSentenceV1` | shared | Child-facing transition from explanation to the same off-screen activity. |

Revision-2 invariants:

- one primary anchor, one objective and one template per approved session;
- P2 supplies observations but never selects pedagogy;
- P3 and P4 consume the approved spec and cannot change its concept;
- Gate B locks objective, activity, template and spec versions;
- cache, renderer and fallback results preserve the same identity;
- gallery is a session-journey read model, not an independent asset gallery.

The V1/V2 vision reconciliation was resolved by owner decision on 2026-09-12: P2-T2 consumes
FEAT-003 V2 and maps it into FEAT-018-owned `RawUnderstandingResultV1`. P1 integer versions are
adapted to P4's canonical `vN` strings and back through a strict lossless adapter; zero,
leading-zero, malformed, and non-integer values are rejected. Session/job/artifact repository
interfaces have process-local adapters only; storage remains non-durable and DTOs have no
`owner_ref`. A breaking contract change still requires a new version and migration fixture.
