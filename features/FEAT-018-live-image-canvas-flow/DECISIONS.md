# FEAT-018 decisions

- 2026-09-09 research record: user requested one P2 research round and proposals;
  any FEAT-003 change or connection requires user review first. Proposed offline
  slices and contract decisions are recorded in `plan/P2_OFFLINE_FIRST_PLAN.md`
  and local working research notes. Technical recommendations
  remain pending owner review; no implementation or contract migration is approved.

- 2026-09-09 publication decision: at the user's request, the P2 engine-handoff
  review and round-1 research working notes remain local and are ignored by Git.
  Only selected completed P2 records are published after owner review and indexed
  as canonical evidence, following the FEAT-003 publication distinction.

- 2026-09-07: Use one shared contract registry and JSON Schema compatibility gate before any person implements. Individual plans may not introduce parallel field names or versions.
- 2026-09-07: Freeze `VisionUnderstandingResultV1` for FEAT-018; the fixture reference to V2 requires a separately approved migration.
- 2026-09-07: Correct the canonical ACT-0004 mapping before integration: primary `OBJ_OBJECT_PERMANENCE`, secondary `OBJ_RECEPTIVE_LANGUAGE`.
- 2026-09-07: Full device pilot covers all 20 golden activities; all 100 MVP activities receive offline catalog/rule/provenance coverage before broader device rollout.
- 2026-09-07: User-provided non-sensitive image is a runtime source artifact, never committed; evidence stores hash/metadata only.
- 2026-09-07: PixiJS 8 + GSAP 3 remains the renderer baseline inside a controlled WebView/bridge; source artwork is preserved and derived visuals cannot silently replace it.

- 2026-09-09: Approve FEAT-018 revision 2 for the P1 implementation slice only; keep P2/P3/P4/shared integration and live/production execution pending separate approval.

- 2026-09-09: Implement P1 as a fixture-only compiler behind typed contracts. Catalog loading stays in infrastructure, selection/fit/Gate B stays in the application/domain boundary, and no downstream provider, renderer, cache or mobile code may select a different identity. The butterfly fold-and-print case is a test fixture only and does not change the 100/20 catalog counts or production eligibility.

- 2026-09-10 publication decision: publish the completed P2 D1 image admission and decoding
  specification (revision 2) as a selected canonical record,
  `evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` (`EV-018-P2-D1-SPEC-01`), built on the
  previously accepted isolated design. Publication records the specification as complete and
  implementation-ready; it does not start, authorize, or approve D2 implementation, and does
  not amend `approvals/TASK_APPROVAL.md`. Dependency decision U1 (`av==18.1.0` in a new
  optional `image-admission` extra) remains an explicit open owner decision. The source
  revision-2 working note stays local; only this canonical record is published.

- 2026-09-10 completed-output decision: accept the isolated P2-T1 D2 image-admission
  implementation after review and publish `evidence/notes/P2_D2_IMPLEMENTATION_20260910.md`
  (`EV-018-P2-D2-IMPL-01`) through the feature evidence index. The accepted slice includes
  bounded single-snapshot acquisition, internal typed admission policy, the injected PyAV
  decoder, the exact optional dependency, deterministic fixtures and regression coverage.
  This decision authorizes recording and committing the reviewed D2 output only. It does not
  approve D3 measurement, mark P2-T1 complete, connect FEAT-003 producers, or authorize
  Qwen/ASR, mobile, Gate A, shared integration, public-schema migration, push or PR creation.

- 2026-09-11: Use `origin/feature/feat018-p2-image-validation` as the canonical P2 branch for FEAT-018 offline integration. Merge commit `627260c` connects the reviewed P2-T1 D2 image-admission slice to `codex/feat-018-contract-plan`; the other P2 branches remain research-only references. This does not authorize D3 measurement, FEAT-003 producer migration, live provider execution, mobile/public-schema integration, P3/P4 implementation, or production deployment.

- 2026-09-11: Integrate the approved P3 renderer and latest approved P4 media branches into the FEAT-018 integration branch. Keep P3 source-art preservation and renderer fallback, and keep P4 objective/activity/template identity propagation through cache and fallback. Root replay entrypoint `scripts/replay_learning_media.py` is part of the P4 integration so the feature replay test runs from a clean checkout. No live provider, Android/mobile, production asset or production deployment scope is opened.


- 2026-09-11: Implement the approved P1 strict continuity polish as an application/compiler-only policy revision. `P1_STRICT_CONTINUITY_V1` requires exact anchor label/tag and semantic-kind compatibility, objective membership, consistent bridge/media/activity identities and a matching `ExperienceSpecV1.spec_sha256` before Gate B approval. Existing contract versions and P2/P3/P4 consumers remain unchanged; unrelated, ambiguous or tampered fixture flows block closed.


- 2026-09-11: Implement the approved P1 catalog and Gate integrity polish without changing contracts or downstream code. Exclude `OBJ_*` and broad area taxonomy labels from anchor metadata; treat optional selected activity/objective refs as exact constraints when present; use one Gate B approval path; and fail closed on duplicate template IDs, missing objective titles, spec ID drift and spec hash drift.

- 2026-09-11: Add an offline provider-shaped compatibility suite at the P1 boundary. Keep Qwen3-VL-8B-Instruct and Whisper large-v3-turbo identifiers in provenance only; validate provider outputs through the existing strict adapters, require adult confirmation before P1, and preserve source/hash/contract identity. Live provider execution remains separately gated.

- 2026-09-10 D3-R2 approval decision: approve the isolated P2-T1 offline performance/native-memory
  evaluation plan and D3-U1 through D3-U6. The 5-second target binds only to the committed D2
  `admit()` interval. The 256-MiB target binds only to the conservative `[L,U]` working-set bracket;
  a crossing bracket is `INCONCLUSIVE`, never a pass. Cohort A implementation/execution may begin.
  Cohort B execution remains gated on owner visual review of the actual eight non-sensitive images,
  and completed sanitized evidence requires owner review before indexing or closing D3/P2-T1. No
  D2, FEAT-003, provider, mobile, Gate A, public-contract or production-isolation scope is approved.

- 2026-09-10 D3 implementation-state record: the approved D3-R2 harness and deterministic Cohort A
  manifest are implemented and preflight-verified. The 320-sample run is explicitly non-reporting
  because it used an uncommitted working tree; it cannot be indexed, treated as canonical target
  evidence, or used to close D3/P2-T1. Formal execution must identify the exact reviewed commit.
  Cohort B and completed-output publication gates are unchanged.

- 2026-09-11 D3 double-review record: two explicit review passes were completed against the
  implementation and tests. The first pass covered protocol/contract correctness and scope
  isolation; the second covered adversarial inputs, stdin/output limits, cleanup, privacy,
  Win32-memory validation and aggregation/statistics. Verified fixes are limited to the D3 harness:
  asynchronous bounded stdin writing, rejection of untracked worktrees for formal runs, timing
  status recomputation during aggregation, strict environment-envelope validation, and a narrow
  exception for missing digests only on byte-budget rejection. Regression tests cover each fix.
  D2 behavior, FEAT-003 and all downstream scopes remain unchanged; formal exact-commit execution,
  owner review and evidence indexing remain pending.

- 2026-09-11 owner approval and closure decision: approve the Formal Cohort A execution at commit
  `c77230ca1593d5cd31098b5e58f3ff2a13d18a63`, including the sanitized metrics artifact and the
  independent verification report. Index both reports and the JSON metrics under FEAT-018 evidence
  and close D3/P2-T1 for the synthetic Cohort A scope only. Cohort B remains unapproved and must
  retain its visual-source gate. No D2, FEAT-003, provider, mobile, public-contract or shared
  integration scope is thereby authorized.

- 2026-09-12 owner approval and closure decision: approve the Formal Cohort B execution and its
  independent verification with verdict `PASS WITH FINDINGS`. The 24-sample result (eight images,
  three fresh-process repeats each) is accepted with zero data discrepancies. Index the sanitized
  Cohort B report, metrics and independent verification, update the feature context and plan, and
  close D3/P2-T1 for the offline Cohort A+B scope. Carry the three verification findings as
  follow-up work; no Cohort B rerun is required. Provider, mobile, Gate A, public-contract and
  shared-integration scopes remain separately gated.

- 2026-09-12 P2-T2 contract decision: supersede the 2026-09-07 FEAT-018 V1 freeze for this task.
  FEAT-018 P2-T2 consumes FEAT-003's typed `VisionUnderstandingResultV2` through the approved
  `vision_v2.py`/`qwen_vision.py` boundary; ownership remains FEAT-003 and no FEAT-003 change is
  authorized. FEAT-017's flat V1 and remote HTTPS `LightningVisionAdapter` are not used. FEAT-018
  owns a separate `RawUnderstandingResultV1` with typed observation groups, `0..1` confidence,
  required source hash, typed failures, preserved ambiguity/conflicts and mandatory Gate A. The
  exact bounded file list is approved for offline implementation only. Live Lightning/GPU/model
  execution, provider/network calls and downstream integration require separate approval.

- 2026-09-12 P2-T2 offline closure decision: approve the implementation and ASR correlation fix at
  commit `11468d3a5a327697a491f09251a3210987337da0`. The mapper rejects a supplied ASR result whose
  correlation ID differs from the vision result before constructing Raw output; matching, absent and
  typed-failure ASR cases remain supported. Focused and related tests, lint/type checks, repository
  validators and diff checks passed. This closes only the offline P2-T2 contract/mapping slice;
  live Lightning/GPU/model execution and all downstream/provider/mobile/shared scopes remain gated.

- 2026-09-18 owner approval: proceed with FEAT-018 Shared Integration Addendum Rev 2 for the
  non-video Android Emulator demo using a non-child synthetic/test image, backend-only Lightning
  boundary, PixiJS original-art renderer, reviewed-asset allowlist, P4 fallback, handoff, gallery and
  feedback. Optional narration may only be fictional adult voice. No video, real child media, mobile
  provider credentials or durable persistence in this demo. Live dynamic Lightning remains blocked
  until an ADR-0005 addendum and quota/cost gate are approved.
- 2026-09-18 future auth/save constraint: implement current session/job/artifact behavior behind
  replaceable application ports and keep `actor_ref` separate from future `owner_ref`. Later account
  access uses the existing provider-neutral verified-principal boundary and explicit save/ownership
  contracts; Firebase is Authentication-only and product data remains backend-owned PostgreSQL/S3-
  compatible storage. Auth, durable save and real child-media persistence are not approved for this
  demo.
- 2026-09-18 image-only scope correction: remove the optional adult-fictional narration/ASR lane from
  the Android demo. No microphone permission, audio capture/upload, or ASR request is in scope;
  `RawUnderstandingResultV1.narration_status` remains `NOT_SUPPLIED`. Refresh the approved plan hash
  and preserve the Lightning ADR/cost gate and per-sprite visual/rights gate.
- 2026-09-18 live-test budget clarification: the owner reports approximately 25 Lightning credits
  available and enough for testing; the FEAT-018 dev-only ceiling is 25 existing credits total with
  no purchase/top-up. The owner will manually initiate live requests; Codex must not call Lightning.
  Require a user-triggered request, no automatic inference retry, admitted synthetic/non-child image
  only, V2 result validation and Gate A. This does not change Runpod production policy or permit
  audio, video or real-child data.

- 2026-09-21 UI correction decision: the approved mobile integration uses BaoVC's original React
  Native presentation shell (`BaoApp.tsx`, artwork components and screen flow) as the only user
  journey. The former standalone `DemoWorkflowScreen` is not mounted. The shared `AppContext` now
  owns the real session/version/idempotency client calls so the BaoVC screens drive admission,
  explicit Lightning understanding, Gate A, P1/ExperienceSpec, Gate B, Pixi handoff and feedback.
  The image-only scope is visible in the UI: no microphone/ASR/video call is presented. The Pixi
  WebView receives only the backend launch contract and reads the preserved original art through
  its short-lived capability. Auth/save remains an adapter seam, not a durable implementation.

- 2026-09-21 narration workflow correction: retain image as a hard requirement and add an explicit
  optional narration union to the reachable BaoVC Capture screen. `TEXT` is used directly with
  `TEXT_TYPED` provenance and skips ASR; `AUDIO` is uploaded to the process-local backend session,
  then transcribed once by faster-whisper on Lightning only after the explicit analysis command.
  ASR failure blocks before Vision. The implementation adds `/media/audio` and the Lightning `/v1/asr`
  route, preserves future auth/save seams, keeps mobile credential-free, and excludes video.

- 2026-09-22 owner approval and implementation decision: wire the existing FEAT-027 bounded Qwen
  payload normalizer and FEAT-003 closed mapping diagnostics into the FEAT-018 Lightning `/v2/vision`
  live route. Permit one internal schema-repair generation only after the first mapping/schema
  failure, cap the request at two provider generations, keep strict/offline adapter behavior
  unchanged, and fail closed if the repair still violates the typed V2 contract. No public schema
  widening, mobile change, video lane, auth/save implementation or Codex-triggered provider call is
  authorized. See `plan/LIVE_VISION_SCHEMA_REMEDIATION_PLAN.md` and the feature-local evidence note.

- 2026-09-22 owner approval and implementation decision: keep `P1ContextOptionsV1` and FEAT-003
  unchanged while wiring the existing reviewed semantic catalog through `SemanticCatalogPort` for
  the BaoVC T2 flow. Rank grounded claims before Gate A, preserve raw/provenance data, compose a
  bounded Vietnamese topic, and resolve exact/alias/concept-family/age-baseline matches through the
  backend. Expanded fallback must be labeled and must still pass age, safety, material, readiness,
  supervision and Gate-B identity rules. Remove hardcoded butterfly/mock presentation from the
  backend-result path. No video, durable auth/save, mobile credentials or Codex-triggered Lightning
  request is authorized. Evidence: `evidence/notes/TOPIC_AND_T2_ACTIVITY_MATCHING_IMPLEMENTATION_20260922.md`.

- 2026-09-23 owner approval: implement the Pixi-only `Personalized Drawing Exploration` slice on
  `codex/feat-018-pixi-exploration`, covering subject-only Vietnamese labels, learning-thread
  exploration planning, bounded localization/cut-outs, tap-to-discover, 2.5D Pixi rendering,
  mobile orientation/UX, tests and evidence. Whiteboard MP4 generation, TTS, video worker/encoder,
  playback and READY/retry semantics are assigned to another task and are excluded here. Preserve
  the existing video placeholder/handoff seam, Gate A/B and ExperienceSpec identity; do not change
  FEAT-003, auth/persistence, mobile credentials, live provider calls or FEAT-026.

- 2026-09-23 implementation decision: keep Qwen semantic output and geometry localization as
  separate contracts. `SceneExplorationPlanV1` may use only confirmed short subject labels and
  typed relations; `SceneFocusPlanV1` may expose a CROP layer only with a bounded normalized region,
  extraction version and confidence. Missing/invalid localization is a valid `FALLBACK_REQUIRED`
  state that renders the preserved whole drawing. This prevents visually plausible but ungrounded
  subject placement from being presented as truth.
- 2026-09-23 implementation decision: the source capability remains the only runtime image input.
  Source-derived crops reuse that capability and are not separate generated assets. Pixi discovery
  events are bounded and Vietnamese; the mobile shell also exposes at most three subject chips so
  discovery remains usable when geometry is unavailable. The future video implementation consumes
  the unchanged placeholder/handoff seam.
- 2026-09-23 implementation decision: Pixi entry is now an immersive landscape intro followed by
  direct image interaction. `INTRO_COMPLETED` and `DISCOVERY_READY` stay separate so a child cannot
  tap a hotspot while the reveal/localization phase is still running. The control row is overlay
  chrome with a three-second idle hide; empty-canvas taps reveal it again. Native orientation and
  navigation-bar state are restored on every exit path.
- 2026-09-23 implementation decision: add `SceneLocalizationPort` as the application boundary for
  future local/Lightning geometry adapters. The port may return normalized regions only for the
  already-confirmed candidate refs; the existing `build_scene_focus_plan` remains the single
  validator. No localizer result means `FALLBACK_REQUIRED`, preserving the original drawing and
  preventing guessed hitboxes.
- 2026-09-24 owner decision: replace the normal three-card topic-direction review with a
  subject-first picker. The user taps a localized subject directly on the original artwork; the
  backend receives `SELECT_SUBJECT`, re-checks image/narration evidence when the selection changes,
  and returns one grounded Vietnamese sentence before Gate A. Localization is an explicit backend-
  only Qwen/Lightning call; if it has no valid mask/region, use the approved spotlight/outline
  fallback and never fabricate a hitbox. The selected region and claim identity are reused by Pixi.
- 2026-09-24 implementation decision: keep MIME detection at the backend Lightning adapter
  boundary. `SceneLocalizationRequestV1.source_image.content_type` is derived from the admitted
  image signature and is never supplied by mobile or inferred from an untrusted filename. Unknown
  signatures and hash mismatches fail closed before the provider call.
- 2026-09-24 implementation decision: localization output may be normalized only for two bounded
  provider formatting variants: a complete fenced JSON object and the previously documented
  nested `region` shape. Both are converted into the same strict normalized-region model; arbitrary
  prose, unknown fields, invalid geometry and unknown target refs remain failures.
- 2026-09-24 implementation decision: provider confidence is contractually decimal `0..1`. For
  compatibility with common model output, numeric percentages from `1..100` are converted to the
  decimal form at the Lightning boundary; target labels may resolve to ids only on a unique exact
  normalized match. Ambiguous labels and unknown ids remain fail-closed.
- 2026-09-24 implementation decision: localization coordinates may arrive as bounded percentages
  and are converted to normalized source coordinates. A box crossing the source edge is clipped to
  that edge; negative, non-finite, zero-size or unsupported-unit geometry remains fail-closed.
- 2026-09-24 implementation decision: localization model/runtime failures are represented as an
  empty `SceneLocalizationResultV1` fallback with HTTP 200. Input/authentication/integrity errors
  remain HTTP failures; provider failure must not break the child-facing workflow.
- 2026-09-25 owner rollback decision: remove direct image tapping and localization from the normal
  initial workflow. `/v2/vision` produces up to three grounded topic directions; the first is
  selected deterministically and the adult may edit the topic before Gate A. The default app
  composition does not inject a scene localizer, so `/v2/localize` cannot add a second AI request
  or block the topic screen. The localization adapter and endpoint remain isolated for a future
  explicitly approved Pixi-only integration.
