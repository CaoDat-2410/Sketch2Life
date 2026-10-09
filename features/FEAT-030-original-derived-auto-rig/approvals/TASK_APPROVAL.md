# FEAT-030 task approval

- Status: REVISION 2 APPROVED; REVISION 3 APPROVED; REVISION 4 IMPLEMENTATION APPROVED
- Approver: Project owner
- Approved scope: Plan revision 2 in full: Gate-A spatial preprocessing; complete initial archetype registry with generic/rigid/unknown coverage; isolated same-L4 auto-rig worker direction; additive V2 contracts/job/package/renderer/mobile path; deterministic fallback to Renderer V1; tests, security, and feature-local evidence. Exact third-party model activation remains subject to the M0 benchmark/ADR gate.
- Plan revision/hash: 2 / SHA-256 `DBA38B3691E5E81D6F86E93BD028FB52393E5C3E78B97093065D3701A5D01F48`
- Approved at: 2026-09-25 13:26:49 +07:00
- Notes: Approved by the owner's explicit “implmengt” after reviewing revision 2. The hash was refreshed after the implementation-status field changed from `NOT_STARTED` to the achieved baseline status; scope and architecture text are unchanged. No visual asset is approved by this record. Material changes to scope or architecture require a new revision and approval.

## Revision 3 approval request

- Requested scope: repair playback clock/pause/seek/scrub/replay/auto-hide behavior; replace whole-image deformation with benchmark-selected subject/part segmentation, part-aware rigs and deterministic natural motion; add 12–15 second guided intro plus idle loop; integrate the already-approved isolated Lightning worker with measured serialized GPU admission.
- State: APPROVED
- Approval hash: SHA-256 `60AD8018C2F111E9683918202F66126D99A11B98C471D0B3D050CF5037055C88`
- Approved at: 2026-09-26 14:14:47 +07:00
- Approval evidence: the project owner explicitly replied “duyệt” after receiving the revision-3 scope, defaults and hash.
- No revision-3 runtime implementation or model dependency activation is authorized by the revision-2 approval.

## Revision 4 approval request

- Requested scope: benchmark and, only after a separate accepted model ADR, integrate a single-L4 SAM 2.1 Hiera Small subject/part-mask worker; use deterministic and original-Qwen-pass spatial prompts, retain deterministic rig construction/motion, and preserve all existing quality gates and fallback tiers. SAM 3 is excluded from the MVP.
- State: APPROVED_FOR_BENCHMARK_AND_STAGED_IMPLEMENTATION
- Plan revision/hash: 4 / SHA-256 `44CFFBD6B9BD1D42C8475E5EAD9012F2AB8B5806E0BA7B3DA239C3B7206A5FF5`
- Approval boundary: approval of revision 4 authorizes R4-T1 corpus/benchmark work and staged implementation in the recorded order. It does not permit live model activation until the exact model ADR, license review, L4 gates and evidence are accepted.
- Approval evidence: the project owner explicitly replied “implement” after the SAM 2.1 plan was selected.
- Live default activation remains gated by the model ADR and benchmark evidence described in the plan.
- Hash refresh note: the plan status now records the approved staged implementation and benchmark-gated live activation; no model/architecture scope was broadened.

## Runtime bugfix addendum

- State: IMPLEMENTATION APPROVED BY OWNER FIX REQUEST
- Scope: remove the accidental second Qwen inference from the live Lightning vision request by
  making bounded repair opt-in; improve backend SAM 2.1 box-prompt preparation for non-blank
  drawings without restoring an unconditional localization call or permitting full-frame prompts;
  allow only in-memory structural normalization of common Qwen JSON shape drift.
- Approval evidence: the project owner explicitly requested fixing the two observed runtime
  failures (`Qwen` loading twice and SAM2 `PROMPT_REQUIRED`) in the current task.
- Boundary: this addendum does not activate SAM2 by default, change the model ADR gate, or alter
  the approved renderer/domain contracts.

## SAM2 success / Pixi cutout handoff runtime fix — 2026-09-27

- State: APPROVED_BY_DIRECT_OWNER_FIX_REQUEST
- Plan: `plan/RUNTIME_MASK_HANDOFF_FIX_20260927.md`
- Plan SHA-256: `FCB84DADE0A36AC190ACE9D3912744F8DAAB1B71FCC1098DC8D66DD2DC6B9979`
- Scope: short-lived derived-mask read capability, verified mask consumption by PixiJS, subject-only cutout micro-motion when SAM2 supplies no parts, explicit safe downgrade diagnostics, and focused regression evidence.
- Approval evidence: the project owner explicitly requested diagnosis and correction after showing `sam21_segmentation_completed status=SUCCEEDED` while the Android experience appeared to fall back.
- Boundary: no new model/provider activation, no fabricated semantic parts, no change to Gate A/B or learning/activity flow; `FULL_AUTO_RIG` still requires validated independent parts.
- Hash refresh note: only the implementation-status field changed from `IN_PROGRESS` to `IMPLEMENTED_LOCALLY; ANDROID_LIGHTNING_VISUAL_RETEST_PENDING`; approved scope and acceptance criteria are unchanged.

## Renderer boot/bridge timeout follow-up — 2026-09-28

- State: APPROVED_BY_DIRECT_OWNER_FIX_REQUEST; IMPLEMENTED_LOCALLY; ANDROID_ARTIFACT_RETEST_PENDING
- Plan: `plan/RUNTIME_MASK_HANDOFF_FIX_20260927.md`, follow-up section dated 2026-09-28
- Plan SHA-256: `DC763A8168134D36DD4697542D374CE71DE612A5E197DC9D8BD7BAF9F8141D6D`
- Approved scope: implement AC-FIX-030-07 through AC-FIX-030-09: bootstrap before asynchronous Pixi initialization, bounded one-command queue/replay, explicit initialization failure signaling, stage-aware native timeout, and focused regression tests.
- Approval evidence: the owner’s explicit request “check lỗi và fix” for the continuing SAM2-success/runtime-fallback issue and the follow-up report “vẫn fallback.” This is a scoped continuation of AC-FIX-030-04 (no indefinite INTRO_LOADING), not new model/provider or product-flow scope.
- Boundary: no model/provider activation, Gate A/B changes, learning/activity-flow changes, or child-data logging. Android + Lightning visual retest remains required before marking the runtime fix complete.
- Hash refresh: emulator evidence corrected the Pixi-init-stall hypothesis to a lost native-to-WebView launch delivery; the plan now specifies exact-message replay and idempotent deduplication under the already-approved one-command queue/replay scope. No contract, architecture boundary, or acceptance scope was broadened.

## Owner approval — Pixi part-motion restoration — 2026-09-28

- Approver: project owner direct instruction in the current conversation: “fix lại giùm cái”,
  clarified to a 15–30 second duration and fallback order of AI part masks, image-processing
  separation, then the established Pixi method. The owner selected multiple action beats followed
  by rest with a fixed camera.
- Approved plan: `plan/PIXIJ_PART_MOTION_RESTORATION_20260928.md`.
- Plan SHA-256: `C98E2EC9B7BA8C6C6EAEB2D2A1DFA75E8C40817711DCC17AE747D358DF998F1C`.
- Approved scope: carry validated independent part masks through the existing FEAT-030 SAM2.1 and
  renderer pipeline; deterministic image-processing fallback; honest legacy Pixi fallback; fixed
  camera/no full-art zoom or rotation; 20-second default choreography within 15–30 seconds with
  multiple action beats and a still ending; tests and feature-local evidence.
- Preserved boundaries: no Codex-triggered Qwen/SAM/Lightning request, no extra Qwen generation,
  no change to the live SAM activation/L4 benchmark gate, no real child data or provider credentials,
  and no change to Gate A/B, topic/learning contracts or immutable source-art provenance.
- Implementation status refresh — 2026-09-29: the plan's implementation-status field now records
  local offline verification complete and real-mask/Android acceptance pending. Current plan
  SHA-256: `2AF2286718B1A969D037FA768DDFE9B6F4E7422948CA2C095DD1CAB7815E9244`. The approved scope,
  architecture, exclusions and acceptance criteria are unchanged from the owner-approved hash above.
- Implementation evidence: `evidence/notes/PIXI_PART_MOTION_RESTORATION_20260929.md`.

## Owner approval — consume subject-only cutout tier — 2026-09-29

- Approver: project owner, direct request in the current conversation (“sửa r sau đó restart backend”).
- Approved plan: `plan/PIXIJ_PART_MOTION_RESTORATION_20260928.md`, follow-up section “consume the subject-only cutout tier”.
- Plan SHA-256: `4E80D6865B60FC579524CA117248270898E46F3BC8BE0AF26E88B90EF8AEC06E`.
- Scope: render a validated `CUTOUT_MICRO_MOTION` package from its verified subject mask without
  requiring independent part masks; preserve strict `FULL_AUTO_RIG` part-mask validation; add
  focused regression tests and feature-local evidence; restart the local backend.
- Boundaries: no provider/model calls or configuration changes, no contract/Gate/source-provenance
  changes, and no weakening of full-rig validation. Restart clears process-local demo sessions.
- Implementation-status hash refresh: after recording the approved implementation and validation
  outcome in the plan status field, its SHA-256 is now
  `ADCFCF88538D1ACD60FF277427A80D05C5F7A5887D793D7CBA801847C52AF492`; scope and acceptance
  criteria are unchanged.

## Owner approval — no V1 fallback, earlier preparation and bounded cutout inpainting — 2026-09-29

- Approver: project owner, direct instruction in the current conversation (“tiếp đi, ko đc fallback,
  có thể kéo dài thời gian ra, làm 1 cái màn hình load hoặc chủ động load từ lúc mà xác nhận đi”).
- Approval timestamp: 2026-09-29 12:50 Asia/Saigon.
- Approved plan: `plan/NO_V1_FALLBACK_PRELOAD_AND_CUTOUT_INPAINT_20260929.md`, revision 1.
- Approved plan SHA-256: `65C492C49E3C382ECDAD5D0B7E9AAE98565F81B9708A975847FB52B3349D938B`.
- Scope: bounded deterministic background inpainting inside a verified subject mask; remove automatic
  V2-to-V1 whole-art recovery; retain original and show typed failure/retry; prepare renderer package
  immediately after Gate-B approval; add visible loading while Gate-A/Gate-B/render work is in progress;
  extend renderer timeout to 90 seconds; tests and feature-local evidence.
- Boundaries: original pixels and provenance remain immutable; no changes to AI providers/model
  settings/contracts/Gates; no provider call by Codex; invalid masks still fail closed and show source
  plus retry instead of silently animating the full drawing. Legacy V1 commands remain supported only
  when explicitly selected, not as V2 error recovery.

## Integrated quality/personalization plan — approval tracked by FEAT-018

- The SAM 2.1 mask benchmark and high-pigment renderer work are detailed under this feature, but
  are not a separate approval request.
- The single combined approval is recorded at FEAT-018
  `plan/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md` and
  `approvals/TASK_APPROVAL.md`.
- Original approval ledger hash (superseded after hash reconciliation):
  `78F02568914A81F0007B86D68F9541414AACA50212C4A4E755456B2BCEE55F92`.
- Current approved integrated plan revision 1 SHA-256:
  `40B627FC34DC63418464F7F583F1C5A3A3B3F0F5ED205C9DCDA8E5DEB75A4503`.
- The owner reconfirmed the current exact artifact with “duyệt” at 2026-09-29 07:56:46 UTC;
  mismatch and scope-preservation details are recorded in FEAT-018's approval ledger.
- Implement only within that exact scope; existing benchmark/model ADR gates remain mandatory.

## SAM 2.1 prompt-refinement follow-up — APPROVED

- State: APPROVED
- Plan: `plan/SAM21_PROMPT_REFINEMENT_FOLLOWUP_20260930.md`
- Plan revision: 1
- Approved pre-implementation plan SHA-256: `79500D1A0634AC7C30C184C405048A6A30AC267ECE5CA5A39948F77CD1D8030E`
- Post-implementation plan SHA-256 (status/evidence update; approved scope unchanged):
  `9DB8F44BF750DC429F4D5A72EED1F43D50AB97917F797A094BEA707058FB08D6`
- Approved at: 2026-09-30 23:17:06 Asia/Saigon (2026-09-30 16:17:06 UTC)
- Approver/evidence: project owner replied “ok, implement” to this exact plan.
- Requested scope: target-grounded positive/negative point generation, improved bounded candidate
  scoring, one iterative mask-input refinement round with at most two additional SAM predictions
  per source image, synthetic ground-truth evaluation, focused tests and FEAT-030 evidence.
- Explicit exclusions: SAM 2 fine-tuning/training, checkpoint/dependency/model changes, SAM 3/3.1,
  extra Qwen calls, retry loops, parallel GPU inference, mask-policy weakening, and real child
  artwork in repository/evidence.
- Approval boundary: implement only the plan's stated scope; live model activation remains behind
  the existing FEAT-030 ADR and L4 benchmark gates.
- Implementation status: locally implemented and repository-tested; reviewed held-out quality,
  target L4 latency/VRAM, and Android visual acceptance remain pending. No model/provider request,
  fine-tuning, dependency addition, or checkpoint download was performed.

## Pixi sprite show and AI motion matching — APPROVED

- State: APPROVED FOR IMPLEMENTATION
- Plan: `features/FEAT-030-original-derived-auto-rig/plan/PIXI_SPRITE_SHOW_AND_AI_MOTION_MATCHING_20261001.md`
- Plan revision: 4
- Exact pre-approval plan SHA-256: `04DD49A6AC903052BDD3DBB674EE85A5537C642330CFF9F09E5170662B98FEEA`
- Post-approval plan SHA-256 (approval-state metadata only; approved scope unchanged):
  `7EDC97306D9F832F2AD19B38853ED8D77F5ECB8CE71540BD16B381A7D21E0BB7`
- Approved at: 2026-10-01 00:44:56 Asia/Saigon (2026-09-30 17:44:56 UTC)
- Approver/evidence: project owner replied “duyệt plan, tạo nhánh mới rồi mới implement” to the exact revision-4 plan/hash.
- Required branch: `codex/pixi-ai-show-20261001`; created before implementation.
- Approved scope: evidence-bounded image-processing mask proposals; a gap audit and reuse of existing visually approved sprites; add new sprite sequences only where a demonstrated behavior/scene gap requires them and after per-frame visual/provenance review; a versioned structured Pixi visual-show plan; one bounded post-Gate-B backend multimodal request that may use a minimized image crop; distinct companion sprites are allowed within the scene budget; visual beats only, with voice/captions deferred; subject disagreement returns to caregiver confirmation; AI failure is a visible typed error preserving the original, with no automatic retry or substitute show.
- Constraints: Gate A remains authoritative for the selected subject and Gate B for the selected activity. Model output is schema/allowlist validated; no arbitrary code, unapproved asset, silent subject/activity change, automatic V1 fallback, or real child image in repo fixtures/logs. Asset runtime use remains gated by rights/provenance and FEAT-028 catalog eligibility. Live multimodal provider activation remains gated on privacy/retention, contract/ADR, latency/VRAM and Android evidence.
- Implementation status at approval: not yet started. No code, runtime asset reference, model/provider request, or asset promotion was part of the approval action.

## Subject behavior registry and complete motion-sprite coverage — revision 5

- State: APPROVED FOR IMPLEMENTATION
- Plan: `plan/PIXIJ_SUBJECT_BEHAVIOR_CLASS_REGISTRY_REV5_DRAFT_20261001.md`
- Plan revision: 5
- Exact approved plan SHA-256: `11C2DABC405D0C8C3C57768CD97A4277A34F63B97CD22DF984F3D0FE09FA32FD`
- Post-approval plan SHA-256 (approval/implementation-status metadata only; approved scope unchanged):
  `EEB9D66FC3E664A9BFF73C8AE9082ECA6173C57F59BA38E5B01F42FB44E0C791`
- Approved at: 2026-10-01 22:57:34 Asia/Saigon (2026-10-01 15:57:34 UTC)
- Approver/evidence: the project owner replied “dueyejt” to the explicit question asking approval of
  this exact revision/hash; interpreted in context as “duyệt” (approved).
- Approved scope: map all currently supported Gate-A and FEAT-028 topics, with a reviewed extension
  path; define separate subject families, rig archetypes, behavior classes and action primitives;
  allow multiple compatible capabilities per subject and AI selection per beat; include animals,
  people, plants, scene/effect elements and objects; provide one or more reusable motion-sprite cycles
  for every enabled non-static behavior class, with family/class variants where needed; add deterministic
  compatibility/readiness enforcement, unknown/still outcomes, tests and evidence.
- Asset boundary: the 28 frames in seven existing concept sheets have visual approval only. Any new
  generated sheets remain in FEAT-028 `assets/generated/` pending per-frame visual review, provenance/
  rights review, crop/pivot/loop QA, catalog registration, renderer verification and runtime eligibility.
- Integration boundary: no arbitrary model code/assets, no silent Gate-A/B drift, no changes to frozen
  FEAT-018 contracts without an additive reviewed contract/ADR, no live provider activation beyond
  existing privacy/L4/Android gates, and no real child data in fixtures or evidence.
- Required branch: `codex/pixi-ai-show-20261001` (already active for the approved revision-4 work).

## Sprite-cycle PixiJS integration — revision 1

- State: APPROVED FOR IMPLEMENTATION BY DIRECT OWNER REQUEST
- Plan: `plan/SPRITE_CYCLE_RENDERER_INTEGRATION_20261002.md`
- Exact plan SHA-256: `BD42C65E032E1D5FB603B81BC8CF46356E8DC5FAC9CF42A89EE4D784B6A4C44F`
- Approved at: 2026-10-02 (Asia/Saigon; direct request in this task)
- Approver/evidence: project owner explicitly requested “duyệt sprite, nối vào renderer trên pixijs đi, check potential bugs và fix, gate, log nó luôn cho dễ debug”. The approved scope is the exact plan above.
- Scope: visual approval for the 30-sheet/120-frame expansion batch; additive motion-cycle capability and synchronized Pixi frame player; lifecycle gates and safe diagnostics; regression coverage and feature-local evidence.
- Boundary: visual approval is not rights clearance or production runtime approval. Do not enable any sheet until rights/provenance, technical frame QA, catalog, renderer, and Android gates pass. Frozen V1/V2/V3 contracts remain unchanged.

## Sprite-cycle local runtime activation — revision 1

- State: APPROVED BY OWNER'S DIRECT IMPLEMENTATION REQUEST
- Plan: `plan/SPRITE_CYCLE_LOCAL_RUNTIME_ACTIVATION_20261002.md`
- Exact pre-approval plan SHA-256: `9808D1690A44A08D924A607E0745055EBD3CE8FCE2E2376C6E8819FF38FB810A`
- Post-approval plan SHA-256 (approval metadata only; scope unchanged):
  `A6E9B06636279769AE3D8A2B1696CE04A96465188BD843B1CD9D93006F529A1A`
- Approved at: 2026-10-02 (Asia/Saigon)
- Approver/evidence: the project owner explicitly requested “bật sprite mới trong runtime đi” and
  followed the remaining-gate explanation with “tự làm đi”. This directly authorizes the bounded
  plan above: archive recoverable provenance; QA all 37 cycles; enable only passing, currently
  selectable cycles for local/test Android preview; keep production rights/runtime gates closed.
- Scope boundary: no production or public-distribution clearance, no weakening of production gates,
  no unreviewed asset edits, and no commit/push authorization.

## Adaptive original-art rigging and topic-matched Pixi scenes — APPROVED

- State: APPROVED FOR IMPLEMENTATION
- Plan: `plan/PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md`
- Plan revision: 1
- Exact pre-approval plan SHA-256: `FC634C8899AB4B4FC618AF8311BDBD9C7391CC0C952C2F24AF60EC33D12428EF`
- Approved at: 2026-10-08 22:20 Asia/Saigon (2026-10-08 15:20 UTC)
- Approver/evidence: project owner replied “duyệt” to the exact plan revision and hash in the current conversation.
- Owner design choices recorded on 2026-10-08: attempt both background extraction and part separation; prefer part motion when validated; when full part masks are unavailable, compose the verified source cutout into a Pixi scene matching the child's chosen topic; let AI choose among supported strategies; reuse one existing post-Gate-B planner call.
- Approved scope: implement a versioned strategy/theme/asset plan in the existing single post-Gate-B planner call; provide bounded candidate visual previews so it can assess style fit; prefer validated part rigging and use the verified cutout/topic-scene path when parts are incomplete; preserve source/Gate A/Gate B and deterministic allowlists.
- Explicit boundaries: no extra SAM/Qwen call, new model/checkpoint/dependency, live provider request, real child images, asset promotion, or production activation. Invalid masks/planner failures remain visible and fail closed; no automatic retry or unrelated substitute.
- Existing FEAT-028 rights/runtime, FEAT-030 privacy/L4/provider, additive-contract, and Android visual acceptance gates remain mandatory.
- Post-approval plan SHA-256 (approval-gate metadata only; approved scope unchanged): `CD14106E7BC5B920C1A916D15DAC41F8B143A2ECAA714EB6C6844FE323BC3732`.
- Implementation status update — 2026-10-08: locally implemented and offline-tested within the approved scope. No live provider request, real child data, asset promotion, or production activation. Feature-local evidence: `evidence/notes/ADAPTIVE_ART_AND_TOPIC_SCENE_IMPLEMENTATION_20261008.md`.

## Pixi planner timeout and invalid-output fix — APPROVED

- Approver: project owner, direct request in this conversation: “bug như sau, check log và fix”, followed by the Lightning log with `MODEL_OUTPUT_INVALID` and HTTP 502.
- Approved plan: `plan/PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md`, revision 1.
- Exact plan SHA-256: `30946B6A0F8F4B20C21822BA2B3717C4014109F8DDACD45676AF4BD637A2027F`.
- Approved scope: align only the mobile renderer-preparation timeout with the existing 120-second planner deadline; make the V4 prompt satisfy the existing closed schema; optionally unwrap a single JSON fence; add safe stage-specific failure logs.
- Boundaries: one bounded inference call, no automatic retry/fallback, no contract changes, and no logging of prompts, images, model output, or user content. Remote model inference and deployment are excluded from this local implementation.
- Approval date: 2026-10-09 (Asia/Saigon).

## Pixi schema-invalid prompt contradiction fix — APPROVED

- Approver: project owner, direct request in this conversation: “bị 502 bad gateway, check log và fix đi”, followed by confirmation that Lightning pulled/restarted `c74831e` and the new `MODEL_SCHEMA_INVALID` log.
- Approved plan: `plan/PIXI_SCHEMA_INVALID_PROMPT_CONTRADICTION_FIX_20261009.md`, revision 1.
- Exact pre-approval plan SHA-256: `BA64D2C9798FCA0799B13E2D8DFCA4BFCC722F76911FA46F0F288B399DBD0535`.
- Approved scope: resolve the V4 asset-ID prompt contradiction, state JSON array/null shapes, and add allowlisted schema field-path/error-type diagnostics without values or user/model content.
- Boundaries: preserve the single inference, closed schema, generic fail-closed 502, no retry/fallback/repair, no contract changes, no live provider request, and no real child data.
- Approval date: 2026-10-09 (Asia/Saigon).

## Pixi root-validator diagnostics and prompt constraints — APPROVED

- Approver: project owner, direct request in this conversation: “vẫn bị 502, check log và fix”, followed by the deployed-build log `MODEL_SCHEMA_INVALID schema_issues=root:value_error`.
- Approved plan: `plan/PIXI_ROOT_VALIDATOR_DIAGNOSTICS_AND_CONSTRAINTS_20261009.md`, revision 1.
- Exact pre-approval plan SHA-256: `3963AA22099CEB713E6440E0EA78D2C5D00A5BB27DFD14340B8BEDDEC464B3A3`.
- Approved scope: clarify the final still-tail and unique selected-ID constraints; map known root validation rules to safe fixed log codes without logging messages or values.
- Boundaries: no retry, model-output repair, fallback, contract change, live provider request, or real-child data.
- Approval date: 2026-10-09 (Asia/Saigon).

## Pixi dynamic still-tail prompt bound — APPROVED

- Approver: project owner, follow-up log in this conversation reports `MODEL_SCHEMA_INVALID schema_issues=root:still_tail_too_short` after deploying `18762db`.
- Approved plan: `plan/PIXI_DYNAMIC_STILL_TAIL_BOUND_20261009.md`, revision 1.
- Exact pre-approval plan SHA-256: `0393C62F98D4A6EDBFC61D1BC509227388466B9B32D4472E917C7D583F482189`.
- Approved scope: insert exact numeric duration, last-beat cutoff, and final still interval into the V4 prompt using the request duration.
- Boundaries: preserve fail-closed validation and the single inference; no output clamping/rewriting, retry, fallback, contract change, live provider request, or real-child data.
- Approval date: 2026-10-09 (Asia/Saigon).

## Pixi rig-capability prompt and diagnostics fix — APPROVED

- Approver: project owner, direct fix request in the current conversation: “fix fix fix đi hiếu 3d”, with the screenshot showing `/v4/pixi/show-plan` HTTP 200 and the app's unsupported-mask-motion message.
- Approved plan: `plan/PIXI_RIG_CAPABILITY_PROMPT_FIX_20261009.md`, revision 1.
- Exact approved plan SHA-256: `7E91B1E3E60ADCE003C1C043610331E17053A8657017CDE3D06A7B986BA74E72`.
- Scope: derive V4 prompt strategy/action choices from the validated rig tier, part roles, and eligible environment candidates; retain compiler/renderer validation; add fixed sanitized compiler rejection reasons.
- Boundaries: no retries, output repair, substitute show, contract/model/dependency changes, provider calls from this workstation, or user-content logging.
- Approval date: 2026-10-09 (Asia/Saigon).
- Implementation-status hash (approved scope unchanged): `B6401F505EFE6D918A4498DADF0E1B7F344EAFD0AAC02B9BC6D59DE0F15ABBA9`.
- Implementation evidence: `evidence/notes/PIXI_RIG_CAPABILITY_PROMPT_FIX_20261009.md`; live runtime retest remains pending.

## Pixi final-beat SETTLE prompt fix — APPROVED

- Approver: project owner, direct follow-up “vẫn bị” with the deployed log `MODEL_SCHEMA_INVALID schema_issues=root:final_beat_not_settle`.
- Approved plan: `plan/PIXI_FINAL_SETTLE_PROMPT_FIX_20261009.md`, revision 1.
- Exact approved plan SHA-256: `B2001FD8B8EF0DB19B8951D713052FB9E232C34AFDF8CA50EF621D47D06AADE0`.
- Scope: add request-derived indexed final-beat constraints and repeat the exact `beats[2].action = SETTLE` requirement at the end of the V4 prompt.
- Boundaries: keep one inference and strict schema validation; no retry, output repair, fallback, contract change, live provider call, or user-content logging.
- Approval date: 2026-10-09 (Asia/Saigon).
- Implementation-status hash (approved scope unchanged): `3EF47B2CE15DDE3C2BD92CC1F12FEB1937DEB66BF1266789811ABB39CD718A9F`.
- Implementation evidence: `evidence/notes/PIXI_FINAL_SETTLE_PROMPT_FIX_20261009.md`; live runtime retest remains pending.

## Pixi V6 launch dispatch fix — APPROVED

- Approver: project owner, ongoing direct request to fix the Pixi launch failure, with the current screenshot showing the preparation timeout after the prior fixes.
- Approved plan: `plan/RENDERER_V6_LAUNCH_DISPATCH_FIX_20261009.md`.
- Exact plan SHA-256: `056C2F1037FF7AE31DA4B62D6C23FDC8BDC8081DACD91AA73CA4F716DAE4B967`.
- Scope: dispatch V6 commands in the renderer launch parser while preserving V1–V5 and the existing V6 sprite-cycle behavior.
- Boundaries: preserve V1–V5 compatibility, V6/backend schemas, source art, orientation, planner/provider behavior, and all existing model/runtime gates.
- Approval date: 2026-10-09 (Asia/Saigon).
