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
