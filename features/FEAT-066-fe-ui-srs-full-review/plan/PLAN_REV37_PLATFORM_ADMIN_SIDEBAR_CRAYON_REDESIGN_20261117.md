# FEAT-066 Plan Rev37 — Platform Admin sidebar crayon redesign

- Product kind: software — authenticated platform-administration console.
- Owner request: use the applicable frontend skill to redesign the Platform Admin sidebar shown in the attached screenshot because its current appearance is poor.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; branch codex/fe-ui-web-remediation; baseline b72f9e46f9c63e019807d7c4a2c309b0aa46a133.
- Requirements context: continue the owner-selected, unsigned FEAT-063 v2.7-draft Rev69 attachment recorded in FEAT-066 Rev36 for this UI task. Repository SRS authority remains Rev60; this navigation presentation change does not update requirements or settle policy.
- Skills: design-taste-frontend, ui-ux-pro-max, frontend-design, senior-frontend and clean-code. Treat the sidebar as a dense application control: use the existing Sketch2Life crayon tokens/components; no marketing layout, new assets, dependencies, or second design system.

## Review findings

1. Platform Admin token selectors override the shared sidebar colors, leaving ordinary navigation links bright cobalt while the selected item uses teal.
2. Platform typography overrides the navigation group labels into oversized uppercase headings, making the menu hierarchy noisy.
3. “Chờ API” is plain text, visually merged with the link label; labels wrap unevenly and row spacing is inconsistent.
4. The account/session footer sits apart from navigation actions and has no contained grouping.
5. The supplied screenshot shows the mobile drawer open, so the redesign must preserve its close, overlay, scroll, focus, and route behavior.

## Scope

- Restyle only the Platform Admin .s2l-sidebar and its descendants, scoped with existing html[data-portal="platform"] selectors in the platform stylesheet.
- Improve branding, descriptive caption, sentence-case group labels, neutral navigation links, selected route state, waiting-state badge, footer account status/actions, and light/dark palette treatment.
- Preserve existing route destinations, active-state calculation, API availability labels, logout/password handlers, mobile drawer mechanics, all other roles, and application/API contracts.
- Preserve all prior uncommitted work. No generated assets or app test suite; no commit/push.

## Acceptance criteria

- AC1 — Role scope: Only Platform Admin sidebar styles change; Teacher and School Manager sidebars remain unaffected.
- AC2 — Crayon hierarchy: Brand/caption, group labels, ordinary links, active route, and “Chờ API” state read as one warm paper/ink/blue system without bright blue default links or oversized uppercase headings.
- AC3 — Interaction: All original links, labels, route destinations, pending-state meaning, password action, logout action, active-state marking, and focus handling remain intact.
- AC4 — Accessibility: Navigation/actions remain keyboard accessible, all visible controls have practical 44px targets, visible focus, readable contrast, and reduced-motion support.
- AC5 — Responsive behavior: Open/closed drawer, scrim dismissal, Escape close, scrollable nav, and fixed footer still work at 390px and 768px; desktop rail remains aligned at 1440px; no horizontal overflow.
- AC6 — Visual review: Capture and inspect desktop and open-drawer mobile/tablet screenshots. Record route, viewports, observations, changed paths, and checks in FEAT-066 Rev37.
- AC7 — Validation: Focused frontend build, Platform Admin sidebar lint, and git diff --check pass. No app test suite, commit, or push.

## Workflow

1. Record current dirty worktree baseline and append this plan plus the direct owner approval before source edits.
2. Add platform-only CSS overrides in the existing Platform Admin stylesheet. Do not change shared component behavior.
3. Visually inspect the active Platform Admin route at 1440x900, 768x1024 and 390x844 with the mobile drawer open.
4. Update FEAT-066 context, decision, evidence, index, and status.

## Risks

The screenshot arrives from an open Platform Admin session. Local headless visual review may need presentation-only shell state; it must not provide a Firebase token, fake account data, or submit protected mutations.
