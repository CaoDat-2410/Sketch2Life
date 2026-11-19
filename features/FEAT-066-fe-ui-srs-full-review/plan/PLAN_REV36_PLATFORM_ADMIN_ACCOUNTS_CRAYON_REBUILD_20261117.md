# FEAT-066 Plan Rev36 — Platform Accounts crayon UX rebuild

- **Product kind:** software — authenticated platform-administration console.
- **Owner request:** inspect the Platform Admin Accounts page against the supplied SRS and rebuild its information layout and UX in the existing crayon visual language.
- **Worktree:** `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`, baseline `b72f9e46f9c63e019807d7c4a2c309b0aa46a133`.
- **SRS used for this task:** user-supplied `F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (1).md`, v2.7-draft, header dated 2026-11-13 and describing amendments through Rev69; SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. The repository's `docs/context/SRS_AUTHORITY.md` still names Rev60 as canonical. The user explicitly selected the supplied file for this task; this plan records that task-specific comparison source without changing the repository authority register or claiming formal SRS sign-off.
- **Applicable skills:** design-taste-frontend, ui-ux-pro-max, frontend-design, senior-frontend, senior-architect, clean-code. Treat this as a dense authenticated software console: reuse the product's crayon tokens and existing controls; do not add marketing imagery, decorative generated assets, dependencies, or a second design system.

## Confirmed review findings

1. An API/authentication error leaves the empty table and “0 trên 0 tài khoản” visible, conflating request failure with a successful empty result.
2. Search cannot be submitted with Enter; the create control remains available when no authenticated backend session is present.
3. Assigning School Manager uses a blocking browser prompt for organization ID.
4. The page uses offset pagination with a page size of 50. The supplied SRS §21.1 specifies stable opaque cursor pagination, default 25 and maximum 100; changing that contract requires backend support and is not included here.
5. The SRS separates product roles from scoped capabilities: Content Admin is a permission of Platform Admin, not a product role, and Platform Admin role alone grants no child-media/profile access. The current account API exposes role/state but no capability grant/read contract. The UI must not invent a permission toggle or imply child-data access.
6. The page needs distinct loading, retryable error, authenticated empty, filtered no-results, and populated states with a responsive accessible layout.

## Scope

- Rebuild only `apps/web/src/modules/platform-admin/pages/UsersPage.tsx` and a page-scoped stylesheet if required.
- Preserve the current typed account list/create/update APIs, Firebase/backend authentication boundary, product role vocabulary, and server-side authorization.
- Improve the hierarchy, page actions, filter submission, account rows, organization assignment input, status feedback, and responsive treatment in the existing crayon palette.
- Keep capability assignment/moderation, API contracts, backend, other roles, mobile/native, assets, and product policy out of scope.
- Preserve all pre-existing uncommitted work. No commit, push, deployment, or automated application test suite.

## Acceptance criteria

- **AC1 — Visual system:** the page has a clear title/action hierarchy and uses scoped existing crayon/paper tokens, semantic states, consistent borders/radii, readable type, and visible focus. No unrelated visual assets or new dependencies.
- **AC2 — Truthful API state:** loading, auth-required/network/server failure, successful empty, filtered no-results, and populated results are distinguishable. Failed requests never render a successful empty-state message or zero-result pagination claim. Retry is explicit.
- **AC3 — Authentication:** account actions and data filters cannot be submitted without a usable backend Firebase session; the user receives a clear recovery path. No mock role/session, fake success, or fabricated account data.
- **AC4 — List interactions:** filters submit by button and Enter, reset to the first page, and preserve current endpoint parameters. The page uses a 25-account page size without claiming cursor compliance; the offset/cursor contract gap remains documented.
- **AC5 — Account operations:** create, role change, lock/unlock, status feedback, and School Manager organization ID remain wired to existing APIs. Organization ID is collected inline, not through a blocking prompt. Mutations expose pending state and prevent duplicate submission.
- **AC6 — SRS boundary:** show only the four SRS product roles; explain role/scope boundaries accurately; do not add Content Admin as a role or expose child media/profile access. Record capability management as blocked on a backend/API contract.
- **AC7 — Accessibility/responsiveness:** semantic form/table labels, keyboard operation, visible focus, meaningful live feedback, practical 44px targets, reduced-motion support, and no horizontal page overflow at 1440, 1024, 768, and 390 CSS px.
- **AC8 — Review/evidence:** visually inspect the running account screen and record observations, limitations, changed paths, and checks under FEAT-066 Rev36. Run a focused app build and `git diff --check`; do not run the automated app test suite.

## Workflow and risks

1. Record the existing dirty-path baseline and append this plan plus explicit approval before editing application source.
2. Implement the smallest page-scoped change; do not alter API/domain behavior.
3. Inspect desktop/tablet/mobile states in the local browser, including the current missing-Firebase-session error and a successful account list only if the existing dev session is already available. Never include credentials or tokens in evidence.
4. Update FEAT-066 context, decision, evidence index, and status.

**Risks/open items:** repository-wide SRS authority still points to Rev60; this task follows the user's explicit Rev69 attachment without changing that register. Capability assignment and cursor pagination need backend contracts. The current local preview may not have an authenticated Firebase session, which limits populated-state runtime evidence.
