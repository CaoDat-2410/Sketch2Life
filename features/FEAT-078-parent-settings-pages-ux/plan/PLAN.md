# FEAT-078 Plan Rev1 — Parent account and security page UX

- State: PLANNED; awaiting hash-specific approval record.
- Date: 2026-11-10.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Target: Parent web P13 account and security subviews in apps/parent-ui.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, per the active repository AGENTS.md. The selected worktree contains an older v2.5 SRS snapshot; it is not used as current product authority. This task is visual organization only and does not change product requirements.

## Owner request

“Và sau đó phân bố lại bố cục cái này cho tôi đi dùng skill sửa bố cục UX 2 trang này nó sai UX hoàn toàn bố cục bị lung tung”

## Goal

Reorganize the two supplied Parent web subpages into clear, scannable mobile settings screens while preserving their existing content and behavior.

## Scope

1. Refine the account page into a clear parent information section and a clearly named video/preferences section.
2. Refine the security page into a coherent privacy information section, a distinct profile-access section, and a clearly separated password form.
3. Improve heading hierarchy, supporting copy placement, control spacing, card grouping, and scroll clearance around the fixed bottom navigation.
4. Preserve current Vietnamese copy and meaning, account save feedback, all three preference switches, privacy notes, password validation/error feedback, and back navigation.
5. Use existing visual tokens and SVG icons. No generated assets or new dependency.
6. Review at 360×780, 390×844, and 768×1024 in the local preview; store screenshots and review notes in this feature evidence folder.

## Acceptance criteria

- AC1: The account form and its save action read as one clear section with properly grouped labels and comfortable spacing.
- AC2: Notification, subtitle, and landscape preferences have an explicit section heading and consistent row hierarchy.
- AC3: The security information is chunked under clear headings, with profile access visibly distinct from AI/privacy notes.
- AC4: The password fields, validation feedback, and save action are grouped together and remain reachable without overlap from the floating navigation control.
- AC5: Existing settings actions, form validation, privacy wording, and navigation behavior are preserved; no backend/API/authentication/persistence or policy changes are introduced.
- AC6: The two pages have no horizontal overflow, clipped labels, or overlapping controls at the listed viewport sizes; controls retain keyboard focus and accessible names.
- AC7: Update feature context, decisions, evidence, status, and approval records before closing.

## Exclusions

- No changes to product policy, privacy/security claims, account identity rules, or SRS.
- No backend, API, authentication, persistence, or real password-change integration.
- No redesign of unrelated routes, native settings modals, or the shared navigation.
- No commit, push, deployment, or publication.