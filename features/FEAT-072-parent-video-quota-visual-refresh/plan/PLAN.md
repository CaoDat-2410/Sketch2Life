# FEAT-072 Plan revision 1 — Refresh the Parent video quota screen

- Revision: 1
- Status: APPROVED after recording the owner's direct request in the worktree approval ledger.
- Prepared: 2026-11-10
- Product authority: FEAT-063 SRS v2.7-draft, updated 2026-11-07, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off.
- Active implementation target: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation, currently serving the local Parent UI on port 5171.

## User request

“Dùng skill sửa lại toàn bộ giao diện lượt tạo này sao cho mới mẻ hợp với phong cách trẻ em mà SRS đề ra”.

## Goal

Redesign the Parent-facing P12 video quota and top-up screen so it feels warm, playful, and easy to scan while keeping quota and simulated-payment information clear to the adult account owner.

The SRS sets a child-centered, Montessori-inspired product context for ages 3–10; it does not prescribe a color palette or the appearance of this quota screen. The redesign will use that context without presenting quota purchase as a child action or gamifying spending.

## SRS mapping and source boundary

- Canonical requirements are from FEAT-063 SRS v2.7-draft, §§1–31, as routed by F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md.
- BR-38 and §31.7 define monthly Parent-account quota, separate from school/Teacher scope; each accepted full-video request consumes one unit. A quota rejection must not be accepted or consume usage. The SRS allows Parents to buy top-up quota.
- FR-PL-24 / BR-60 allow Parent packages/top-ups, but package amounts and prices are not decided. Existing +3/+5/+10 amounts and displayed prices are synthetic fixtures only; retain them only with clear demo labeling.
- NFR-38 describes Vietnamese V1 for children ages 3–10, Montessori-inspired and child-centered, with adults guiding and supporting. The SRS does not mandate UI styling for billing.
- fe-ui-full-remediation contains stale local copies of AGENTS.md and docs/context/SRS_AUTHORITY.md that say v2.5. The user's current repository instructions and the main checkout authority point to v2.7-draft; use the v2.7 file and keep the stale copies unchanged.
- Existing FEAT-070/071 records are implementation evidence only; they do not define current product requirements.

## Current implementation evidence

P12 is P12VideoQuotaPage in apps/parent-ui/src/pages/ParentScreens.tsx. It reads session-local quota buckets, usage ledger, and payment simulation state from ParentContext. It displays a used/total ring, three fixed demo packages, MoMo/VNPAY selection, simulation status, purchase CTA, and usage history. Tablet layouts currently target the .gauge selector in apps/shared/parent-ui.css.

## Scope

- Redesign the entire P12 screen hierarchy and interaction styling in apps/parent-ui/src/pages/ParentScreens.tsx and apps/parent-ui/src/styles/tokens.css.
- Add responsive P12-specific layout rules in apps/parent-ui/src/styles/tablet.css if needed; scope new rules to P12 so other routes keep their current layout.
- Add FEAT-072 context, decisions, approval, status, and evidence records.
- Reuse the existing icon system and app tokens. No generated bitmap or external visual asset is needed for this native UI redesign.
- Preserve current local fixture numbers, screen route, ParentContext contract, simulated purchase behavior, and the usage-ledger expand/collapse behavior.

## Explicit boundaries

- Visual and interaction-presentation changes only.
- No API, auth, account, database, persistence, payment-provider, billing-policy, quota-calculation, SRS, or price/package changes.
- Do not imply that demo prices or packages have been approved for production.
- Do not change the existing FEAT-036/067/068/069/070/071 work or unrelated changes in shared files.
- No automated test suite, build, commit, push, deployment, or publication.

## Implementation steps

1. Replace the generic usage-ring/purchase layout with a clear remaining-quota summary, readable included/top-up breakdown, and a calm story-themed visual treatment using existing UI primitives.
2. Redesign the package choices and payment-method choices with clear selected states, adult-readable amounts, keyboard focus, and sufficiently large touch targets.
3. Label all purchase figures and the checkout action as demo simulation; preserve pending/success/failure feedback and prevent a second simulated purchase while pending.
4. Refresh the usage history cards and provide a meaningful empty state without changing ledger data.
5. Add phone and tablet responsive rules scoped only to P12; honor reduced-motion preferences and avoid horizontal overflow.
6. Manually review the live port-5171 screen at phone and tablet widths, including normal quota, exhausted quota, package/method selection, pending/result feedback, ledger expansion/empty-state rendering, keyboard focus, and the surrounding bottom navigation. Record findings and evidence under FEAT-072.

## Acceptance criteria

1. The remaining quota is the primary value, and the included/top-up balances are both visible and labeled without implying top-up units expire monthly.
2. The visual system feels friendly and fresh for the parent product while purchase options remain adult-facing and prices are clearly identified as demo fixtures.
3. Selecting any package or payment option updates a visible, accessible selected state; keyboard users can operate both controls and see focus.
4. The simulated checkout action preserves existing state behavior, shows pending/success/failure feedback, and is unavailable while pending.
5. A zero-quota state is visually clear and still allows selecting a demo top-up package.
6. Usage rows remain readable; “show more”/collapse remains functional; an empty ledger has a clear message.
7. Layout works without horizontal overflow at narrow phone and tablet portrait/landscape widths; interactive targets are at least 44 CSS px where practical.
8. Text and controls retain readable contrast, status feedback is announced, and motion respects prefers-reduced-motion.
9. No route, API, auth, persistence, quota policy, or product-price behavior changes.

## Verification boundary

Use the active local preview for a manual visual and interaction review. Do not run automated tests or builds under this plan. Keep evidence and any screenshots inside this feature's evidence directory.
