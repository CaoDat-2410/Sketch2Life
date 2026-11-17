# FEAT-020 Task Approval

**Task:** Implement a backend-only, real-AI, one-command Sketch2Life workflow demo in Lightning Studio, using a repository pulled from GitHub, with no UI and no fixture-backed acceptance path.

**Feature:** `FEAT-020-backend-ai-workflow-demo`
**Plan:** `features/FEAT-020-backend-ai-workflow-demo/plan/FINAL_IMPLEMENTATION_PLAN.md` plus the approved PixiJS asset-plan revision and the owner-approved `SEMANTIC_ACTIVITY_SCALING_REMEDIATION_PLAN.md`
**Historical base-plan status:** `APPROVED` (2026-09-13); **2026-09-28 amendment:** `APPROVED_FOR_DOCUMENTATION_ONLY`; **amended implementation status:** `NOT_AUTHORIZED`
**Approver:** project owner (explicit approval in current task)
**Approval date:** 2026-09-13

## Requested scope

- direct in-process Lightning model adapters;
- real arbitrary image input, optional real narration audio;
- connected understanding, Gate A, Montessori/P1, Gate B, story/scene, original-art, real micro-video, activity handoff, feedback/history demo flow;
- one CLI command and one real-AI E2E test;
- no UI implementation;
- no fixture ID, fake adapter, or silent fallback as complete success;
- feature-local evidence and required governance validation.

## Explicit exclusions

- mobile/web UI;
- Firebase data stores;
- durable production persistence;
- committing user/child media or secrets;
- separately operated provider server as the main acceptance path.

## Approval record

The project owner explicitly approved the current plan revision. This approval authorizes implementation within the recorded FEAT-020 scope, including the shared PixiJS domain-asset planning boundary. It does not authorize UI implementation, PixiJS runtime integration, runtime AI asset generation, or video generation beyond the explicitly deferred contract.

```text
Status: APPROVED
Approver: project owner (explicit approval in current task)
Date: 2026-09-13
Decision: APPROVED
Plan revision: d9e6724 (docs(FEAT-020): plan full PixiJS asset coverage)
Notes: Full-catalog PixiJS asset coverage is planned for 100 activities, 236 material-group instances and 380 unique material option IDs. Assets remain hand-authored SVG/vector, shared by semantic/material family, with layer/crop/mask/transparent requirements where animation needs them. UI/system-state assets and PixiJS runtime remain out of scope.
```


## Remediation plan approval

Status: APPROVED
Approver: project owner (explicit approval in current task)
Date: 2026-09-13
Decision: APPROVED
Plan: features/FEAT-020-backend-ai-workflow-demo/plan/SEMANTIC_ACTIVITY_SCALING_REMEDIATION_PLAN.md
Scope: hybrid curated semantic eligibility, bounded AI suggestions, safe fallback tiers, full 100-activity catalog remediation, and test-only partial age-matrix reporting.
## Proposed V2 semantic personalization remediation

Status: APPROVED
Approver: project owner (explicit approval in current task)
Implementation approval: granted
Date: 2026-09-13
Plan: features/FEAT-020-backend-ai-workflow-demo/plan/SEMANTIC_PERSONALIZATION_V2_REMEDIATION_PLAN.md
Decision record: features/FEAT-020-backend-ai-workflow-demo/DECISIONS_SEMANTIC_PERSONALIZATION_V2.md
Scope: shared age-invariant scene understanding, reviewed concept ontology, semantic recall improvement, new V2 contracts, first-class fallback mode, mode-aware Gate B/story/bridge/telemetry, and real-AI regression coverage.
Explicitly deferred: UI, PixiJS runtime, video generation, real caregiver feedback, persistence and production catalog approval.

## Addendum — owner-requested story/video planning update (2026-09-28)

- **Status:** `APPROVED_FOR_DOCUMENTATION_ONLY`; this is not an implementation approval.
- **Authorized documents:** `plan/PLAN.md`, `plan/CONTENT_STORY_EXPERIENCE_PLAN.md`, `plan/VIDEO_STORY_PRODUCTION_PLAN.md`, feature context/decisions/evidence, and the linked FEAT-029 master SRS sections B30–B32.
- **Owner-confirmed target:** illustrated 40–60 second story video; age/readiness-based educational knowledge; both quick and free-form script edits; adult approval of the full exact script before image generation; selectable supported language/voice; keep Wan2.2 TI2V-5B baseline; redraw is allowed as a derived artifact while the original remains immutable.
- **Approval boundary:** the earlier 2026-09-13 plan approval does not cover these expanded requirements. Implementation, UI code, provider execution, model downloads, contract migration, cloud changes, release, commit/push, and changes to unrelated/pre-existing user files remain excluded. Keep amendment status `OWNER_CHANGE_DRAFT` until separately reviewed and approved.

## Addendum — owner supported-age implementation update (2026-10-06)

- **Status:** `APPROVED` for the exact cross-feature age-boundary work recorded in FEAT-037 Plan revision 1.
- **Owner instruction:** limit the product age band to `<9` and align the SRS, context, and GenAI materials.
- **Authorized FEAT-020 scope:** update the active age matrix and age-sensitive workflow so only 0–3, 3–6, and 6–9 product bands run; reject requests beyond 107 completed months before age-specific activity selection or AI provider execution; preserve the 9–12 source catalog; update FEAT-020 context/decisions/age variation/story plans and the existing E2E acceptance assertion.
- **Not authorized:** model/provider calls, model downloads, deployment, cloud changes, payment processor selection, live billing, or publishing 9–12 catalog changes.
- **Controlling plan:** `features/FEAT-037-registration-age-genai-payment-alignment/plan/PLAN.md`, SHA-256 `7558d4fba751937c823b6923075efd2a621207c51c6c8ef2edcf4f4fadd50a3e`.
- **Current implementation clarification:** FEAT-037 Plan revision 2, SHA-256 `B9C4454605146ED5E69241381E4A65C666AF751CBC36B4F8BAA2272897BAECB9`, preserves the approved age scope and existing versioned DTO compatibility; the application layer rejects unsupported product ages before age-sensitive work.
