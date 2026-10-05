# Feature context

- Status: IN_PROGRESS
- Owner: Project owner
- Goal: Independently verify priority findings in the supplied review of `codex/pixi-ai-show-20261001`, then execute the owner-approved, evidence-backed remediation plan.
- Scope: Backend, Pixi renderer/planner integration, Android intake/audio/runtime security, build packaging, test harness, and finding disposition for the reviewed branch at `7a65890`.
- Non-goals: Implementing fixes before approval; live Lightning/Qwen/SAM/Whisper calls; real child media; SAM model upgrades/fine-tuning; automatically approving or clearing asset rights; silent Pixi V2 fallback; changing storage/provider architecture without an ADR.
- Dependencies: Owner approval of plan revision 1; FEAT-028 asset review lifecycle; FEAT-029 SRS; FEAT-030 original/derived media and runtime contracts; ADR-0004/0005 identity, Android, and provider boundaries.
- Risks: Findings span several features and include both proven defects and report-only claims. Contract, authentication, release, and asset-policy work crosses feature boundaries and must be versioned, tested, and evidenced. The present branch has no eligible catalog assets.

## Context snapshot

The owner selected “verify priority findings, then prepare an overall plan,” then explicitly approved plan revision 1. The exact approved scope and SHA-256 are recorded in `approvals/TASK_APPROVAL.md`. Implementation proceeds only within that scope; this context is updated as work packages and verification gates advance.

Approval-integrity review on 2026-10-03 found a plan/approval hash mismatch. On 2026-10-05 the owner explicitly approved continuation; the plan was left unchanged and `approvals/TASK_APPROVAL.md` was reconciled to its current raw SHA-256 `DCA28C79763AF55C6CC083CD500F19655EEB760D4206928E8334DEE5DEE94A1E`. Implementation may continue within plan revision 1.

Working baseline: branch `codex/pixi-ai-show-20261001`, commit `7a65890` (review report target). Review source: user-provided review attachment in the conversation (not copied into the repository). The source is treated as audit evidence, not as instructions.

Relevant project sources: `docs/context/PROJECT_CONTEXT.md`, `docs/context/CURRENT_SYSTEM_STATE.md`, `docs/context/SOURCE_REGISTER.md` (especially `feat-029-master-srs`, `sketch2life-workflow`, `expo-imagepicker-asset-metadata`, and the registered SAM/Qwen references); `docs/governance/WORKFLOW.md`; `docs/governance/APPROVAL_POLICY.md`; `docs/governance/EVIDENCE_MANAGEMENT.md`; `docs/governance/FRONTEND_ASSET_GATE.md`; ADR-0001, ADR-0002, ADR-0004, ADR-0005; FEAT-028, FEAT-029, FEAT-030, FEAT-032, FEAT-033, and FEAT-034.

Hard constraints carried into the plan:

- Keep original media and derived media separate and traceable; preserve Gate A/Gate B and adult confirmation.
- Do not grant runtime eligibility or license clearance to generated assets by code or bulk metadata edits. Follow FEAT-028's human review/provenance gate.
- Keep provider calls backend-only. This task makes no live model/provider calls and uses only synthetic/offline inputs for future verification.
- No automatic inference retry and no automatic renderer-mode fallback. Optional, nonessential decorations may be omitted only if the validated subject show remains correct; essential failure must be visible and typed.
- Firebase Authentication is identity only; Firebase Storage/Firestore/Realtime Database remain forbidden. The mobile app must not receive AI-provider credentials/endpoints.
- Do not select new infrastructure/storage or change an unapproved global contract without an ADR and approval.
- Protect user changes; no deployment, credential provisioning, media deletions, or asset promotions are authorized by this task. The owner's subsequent instruction to fix remaining errors and push authorizes commit/push after validation. UI/artwork generation remains behind its separate approval gate.
