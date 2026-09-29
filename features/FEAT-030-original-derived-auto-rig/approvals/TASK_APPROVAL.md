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
