# FEAT-066 — School Manager web remediation against canonical SRS Rev57

- Status: `APPROVED_FOR_SCHOOL_MANAGER_WEB_IMPLEMENTATION`
- Plan revision: 4
- Updated: 2026-11-10 (Asia/Bangkok)
- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
- Branch: `codex/fe-ui-web-remediation`
- Source root: `apps/school-manager-ui`

## Authority and baseline

Use only `F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md` and the canonical FEAT-063 SRS at `F:/Github/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` for current product requirements. The verified baseline is v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. It remains a draft awaiting formal owner sign-off. Use §§1–31 for target requirements; §32 is environment-specific as-built evidence, not product requirements. Do not use the stale SRS copy in this worktree.

## User approval and revision history

- Revision 3 was approved for a read-only School Manager source and local-preview audit only. That audit is complete and remains recorded in `evidence/notes/SCHOOL_MANAGER_WEB_UX_REVIEW_REV57_20261110.md`.
- The user directly approved School Manager web remediation in the current instruction on 2026-11-10. This revision supersedes the read-only restriction of revision 3 for the scope below.
- Do not begin product-code edits until `approvals/TASK_APPROVAL.md` records this revision as approved and contains this plan's verified SHA-256.

## Goal

Correct the confirmed School Manager web UI defects and implement SRS-required organization flows only where an existing backend/API contract supports the operation. Where no compatible contract exists, clearly show that the capability is unavailable and record the missing dependency; never simulate a completed server operation.

## Scope

### Included

- `apps/school-manager-ui` only, including School Manager login, M01 publication review and M02 dashboard, teachers, classes, quota, and settings routes.
- FEAT-066 governance and evidence needed to approve, document, and verify this work.
- Read-only inspection of existing backend/API/OpenAPI contracts to determine which School Manager capabilities can be integrated without backend changes.
- M01 approval versus change-request state/count correctness; notification inbox behavior; narrow and desktop reflow; accessible review tabs; removal of the misleading organization dropdown cue.
- Contract-supported class capacity/create/archive/suspend, Teacher assignment, roster, billing/invoice/payment state, subscription, quota, notification inbox, and feedback reply flows. Unsupported operations must be presented as unavailable, with no fake success message or transaction.

### Excluded

- `apps/mobile`, Parent UI/mobile, Teacher portal behavior, Admin/Platform Admin portals, backend, API contracts, schemas, providers, production systems, and real user/child data.
- Adding or changing dependency manifests/lockfiles unless strictly necessary; first use installed/offline dependencies and preserve the existing package files.
- Inferring open SRS pricing, quota-commercial terms, renewal/downgrade policy, or other unresolved rules.
- Any default School Manager access to child media/story content.
- Automated tests or builds unless the user separately requests them. Required repository security validation still applies before commit/push.

## Acceptance criteria

- AC1: Preserve the canonical SRS identity, draft approval state, and verified Rev57 hash above; do not use §32 as a product requirement.
- AC2: In M01, “Yêu cầu chỉnh sửa” does not increment “Đã duyệt”; approval and change-request outcomes remain separate and the displayed counts match those outcomes.
- AC3: The notification bell opens the inbox only when a compatible inbox API/contract exists. Otherwise remove the unread dot and clearly expose an unavailable state; do not imply unread work exists.
- AC4: At 390px, M02 class heading/actions and quota controls reflow without overlap or clipping; interactive targets are at least 44 CSS px where practical. Check the same routes at desktop width.
- AC5: M01 tabs have linked `tablist`/`tab`/`tabpanel` semantics, correct selected/focus state, and expected arrow-key keyboard navigation; verify with keyboard and screen-reader-facing semantics.
- AC6: The organization name is not styled or marked as a dropdown unless an existing supported action is present; do not add organization switching.
- AC7: For each SRS-required flow listed in Scope, identify an existing API/contract. Implement only compatible operations with real pending/error/response states. Mark unsupported operations unavailable and record their missing API/backend dependency in feature evidence.
- AC8: Do not create fake data, success toasts, billing/payment transactions, prices, or policies to imply execution. Preserve the Manager child-media privacy boundary.
- AC9: Manually review `/login`, M01, and M02 dashboard, teachers, classes, quota, and settings at `http://127.0.0.1:5173/`, bound to loopback. Capture before/after screenshots in FEAT-066 evidence at desktop (1440×900) and narrow (390×844); check the port before starting or reusing the preview.
- AC10: Verify the M01 change-request count, inbox/unavailable behavior, tab keyboard and semantic behavior, and absence of M02 overlap/clipping. Record actual steps and limitations in FEAT-066 evidence.
- AC11: Update FEAT-066 context, decisions, evidence, and status after meaningful implementation and review steps. Keep all modified product files under `apps/school-manager-ui` and all other modified files under FEAT-066.

## Implementation and review constraints

- Use local fixture/preview state only and inspect compatible API contracts without credentials. Do not call a production backend, external provider, or external service.
- Bind the Vite preview only to `127.0.0.1:5173`; reuse an existing local preview if it belongs to this app and check the port before starting it.
- Preserve Vietnamese labels, existing design primitives, visible keyboard focus, responsive behavior, and explicit unavailable/error states.
- Do not run automated tests, scanners, or builds under this authorization. Do not add tests. Report manual verification only.
- Before committing or pushing, run `python tools/validate_repository_security.py` from the repository root as required by AGENTS.md. Do not force-push.