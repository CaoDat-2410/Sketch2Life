# Plan Rev9 — make every primary mockup action understandable

**Feature:** FEAT-069 — Leader review UI/UX remediation
**Date:** 2026-11-14 (Asia/Saigon)
**Status:** APPROVED under the owner's prior broad instruction to complete all project mockup UX and latest request to resolve widespread workflow dead ends.
**Target branch:** `FE_UI_Project_Ver2`

## Context

The owner reports that many screens stop after a generic step and make it unclear how the UI works. The supplied screenshot shows a concrete case: a record-detail button labeled “Xem bước tiếp theo” opens a generic “Bước tiếp theo” dialog with only “Đã hiểu”. In source, `DetailPanel` sends `detail-${page}` to `ActionDialog`; unknown action types use that generic title/body. A repository-wide review is needed because the same pattern can affect other actions and workflow end states.

The user has already authorized complete UI-only mockup work across `UI_Project/`, fictional data, and UX improvements without API integration. This plan narrows that existing authorization to interactive continuity and reviewability; it does not change product contracts.

## Sources and boundaries

- Current requirement baseline: `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft (unsigned).
- Historical comparison requested by the owner: `D:\Capstone Project\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md`. Record differences as historical/open questions only; do not silently replace v2.5 behavior.
- Current implementation: all primary workspaces under `UI_Project/`: Parent mobile WebView UI, Teacher web, School Manager web, Platform Admin web, shared portal.
- Leader UI references: `UI_Project/design-references/ui-mockups-rev38-20261030/` and `UI_Project/design-references/ui-components-rev38-20261030/`; map each screen/component ID to an implemented state and the next interaction, not just a route name.
- API/backend/source contracts remain read-only references. No API, auth, network, persistence, upload, payment, AI or ASR action may be added.
- Preserve established owner decisions: Parent Settings only inside Family Profile; no selected-child summary card on Home; gender is session-only preview; legacy top-level `apps/` and Child Expo are excluded.

## Goal

Make the important mockup paths feel runnable end to end: each primary action opens the intended next screen or completes a clearly labeled local preview state; users can understand what changed, what remains preview-only, and how to continue or return. Do not create a control that claims a server operation occurred.

## Scope

1. Inventory all primary buttons, links, row/detail actions, dialogs, wizard completion actions, role-switch actions, and Parent story/profile/library actions in all five workspaces.
2. Compare Rev38 P01–P12, T01–T07, M01–M02, A01–A02 and UI01–UI09 to current screen states and interactions. Trace each primary action to its result and next step. Replace generic/dead-end “next step” dialogs with context-specific navigation or a context-specific, actionable local preview. Where the source/API cannot support a behavior, explain that exact boundary and provide a safe route back/next preview step.
3. Complete local state transitions for reachable mockup workflows where steps currently stop early. Keep step order from current v2.5-draft unless the owner has separately resolved a conflict. Preserve existing preview-data labels and role boundaries.
4. Compare historical v2.2 flow against the current workspace and v2.5 baseline. Report mismatches (including Parent guide generation/activity timing and Teacher deck behavior) without changing SRS or implementing historical requirements as current by assumption.
5. Record a route/action crosswalk, uncovered server-side capabilities, verification outcomes and unresolved decisions under this feature.

## Acceptance criteria

- **AC1 — action inventory:** the main call-to-action and row/detail action for every route in Parent, Teacher, Manager, Admin and shared portal is checked and mapped to a destination/outcome.
- **AC1a — leader reference parity:** every Rev38 screen/component ID is mapped to a current interaction, intentional static state or explicit gap; flow differences from canonical v2.5 are called out, not silently resolved.
- **AC2 — no generic dead end:** no primary workflow action falls through to an ambiguous generic “Bước tiếp theo”/“Đã hiểu” modal. Informational disclosures are specifically titled and do not pretend to be workflow progress.
- **AC3 — continuous mockups:** each primary flow has a clear start, local step result, next/return route and completion state; unavailable/live-only actions state what is unavailable and where to continue in preview.
- **AC4 — source distinction:** historical v2.2 deltas are recorded separately from v2.5 current behavior; no unresolved product conflict is silently changed.
- **AC5 — integration boundary:** all values/transitions remain fictional and local. No API/auth/network/backend, persistence or provider action is added.
- **AC6 — verification:** all five `UI_Project` production builds pass; Parent Android typecheck and debug APK packaging pass if source changes affect the Parent bundle; manual browser review checks the reported dead end and representative start-to-finish actions across each role and the portal. Do not run automated tests.
- **AC7 — governance:** feature plan/approval/evidence/status/source register are updated; `git diff --check` and `python tools/validate_repository_security.py` pass before each commit/push. No force push.

## Approval basis and exclusions

The owner previously authorized end-to-end mockups for the whole project using fictional data and explicitly asked for complete, convenient UX without API integration. The latest feedback identifies a generic terminal dialog and states that many other sections also stop in the same way. This plan records that authorization for the bounded Rev9 continuity audit and fixes.

Excluded: changes to SRS/API/backend/auth/schema/database, real data or persistence, service/provider calls, payment/email/upload/AI/ASR, legacy top-level `apps/` and Child Expo, automated tests, generated bitmap assets, formal leader/SRS sign-off claims, and force push/history rewrite.
