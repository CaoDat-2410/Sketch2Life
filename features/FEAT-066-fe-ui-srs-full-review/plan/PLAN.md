# FEAT-066 — School Manager web flow audit and school-theme redesign

- Status: `APPROVED_FOR_IMPLEMENTATION`
- Plan revision: 8
- Updated: 2026-11-10 (Asia/Bangkok)
- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
- Branch: `codex/fe-ui-web-remediation`
- Product surface: `apps/school-manager-ui` authenticated School Manager screens only
- Governance/evidence: `features/FEAT-066-fe-ui-srs-full-review`

## Authority and scope

Use only the root authority record `docs/context/SRS_AUTHORITY.md` and its canonical target `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`. The verified baseline is SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. It remains a draft awaiting formal owner sign-off. §§1–31 are target requirements; §32 is environment-specific as-built evidence and is not a source of product requirements. Ignore stale SRS copies in the worktree.

This revision is directly authorized by the user's request to re-audit School Manager against the latest SRS, determine whether its flows are complete, and refresh the visual style for a school serving preschool through primary pupils. It supersedes the revision 7 plan's login-only scope for this new bounded task; completed revision 7 login work remains historical and is not changed.

### Included

- Read-only SRS-to-route/API/contract audit for all School Manager web flows in §21.5 and related use cases/FRs.
- School Manager authenticated shell, M01 public lesson review, and M02 dashboard/teachers/classes/quota/settings visual styling under `apps/school-manager-ui`.
- Presentational class/markup adjustments in `src/components/ManagerLayout.tsx` and `src/components/ManagerScreens.tsx` only when needed for the visual system; preserve all business logic, API calls, route behavior, authorization, counters, tab semantics, unavailable states, and logout behavior.
- FEAT-066 plan, approval, context, decisions, status and evidence, including a current flow completeness/gap matrix and desktop/narrow screenshots.

### Excluded

- Root checkout `F:/Github/Sketch2Life`, all other worktrees, backend/contracts, `apps/shared`, login/auth, Teacher, Platform Admin/Admin, Parent UI/mobile, `apps/mobile`, providers, production data, credentials, and real user/child data.
- New APIs or API calls, billing transactions, prices, commercial rules, fake data/success, and any default School Manager access to child stories/media.
- New dependencies, global/shared tokens, generated/external assets, and changes to manifests or lockfiles.
- Automated tests/builds unless separately requested. Required repository security validation applies before every commit/push.

## SRS review targets

Review §3 role scope, §5.3 organization billing/capacity, §20 permissions/privacy, §21.5 School Manager UI, §23 open billing/pricing policy, §31.2/31.3/31.6, UC-06/08/12/13/15/16, FR-T-02/03/14/17, FR-B-01–14, FR-PL-22, and applicable business rules. Preserve open pricing/policy decisions. School Manager may manage organization metadata and review permitted lesson metadata but has no default access to child story/media.

## Flow audit baseline to verify and document

- Organization dashboard exists at `/m02-organization-management` but current metrics are preview fixtures; no organization summary API was found.
- Class list and read-only roster have API support. Class creation lacks a capacity-enforcement contract; no archive/suspend endpoint was found. Keep create/archive/suspend unavailable.
- Teacher assignment has low-level create/revoke endpoints, but Manager directory/search/provision/selection and safe transfer/offboard saga are absent. Keep end-to-end Teacher flows unavailable.
- Billing, invoice, payment, subscription, renewal, grace-period and downgrade APIs are absent from the checked surface. Keep these settings unavailable; do not infer price or policy.
- Organization quota summary/top-up and verified payment grant APIs are absent. Fixture counts are not real balances.
- Notification inbox API/route is absent; retain a non-interactive unavailable status with no unread signal.
- M01 public lesson access-grant listing/decision contract exists. Local preview decisions are non-persistent; API mode must preserve current behavior. The four-item review rubric is not defined in FR-PL-05 and remains open.
- School Manager feedback list/reply API/route is absent. Keep unavailable.
- Logout remains visible and keyboard-operable; organization context is descriptive, not a selector.

The implementation phase may restyle these flows only. Do not make a blocked flow appear functional. Recheck these source findings before finalizing the audit record.

## Visual direction

Create a calm, welcoming school-office interface suitable for managers of preschool and primary schools: warm paper/chalk surfaces, forest/leaf green as the main accent, restrained marigold and clay for semantic highlights, and readable ink text. Keep the layout professional for adult staff; avoid childish decoration, emoji-as-interface-icons, strong gradients, bevels, and high-saturation multicolor cards. Use the app's local SVG icon set. Do not add images, child media, remote resources, or a Three.js scene to authenticated dashboards. Keep the styling scoped to School Manager authenticated screens; do not change shared login styling or global tokens.

## Acceptance criteria

- AC1: Plan and evidence cite the canonical authority, exact Rev57 SHA-256, draft/sign-off status, and §32 boundary.
- AC2: The flow matrix covers every §21.5 flow and related class capacity/lifecycle, teacher assignment/provision/transfer, roster, billing/invoice/payment/subscription, organization quota/top-up, inbox/notification, lesson review, feedback reply, privacy and logout; each row states target behavior, current route/API support, safely testable surface, and missing dependencies.
- AC3: Only School Manager authenticated web screens and FEAT-066 records change. No pre-existing unrelated dirty file is staged or overwritten. Root FEAT-066 inventory is compared; copy a root-only file only if a needed file is absent in the authorized worktree and can be brought over without overwriting a newer version. Current inventory comparison found no root-only FEAT-066 paths, so no copy is planned.
- AC4: UI refresh follows the visual direction above while preserving route, API, session, logout, preview labeling, M01 count separation/tab keyboard behavior, privacy boundary, and explicit unavailable states.
- AC5: Manually review `/login`, M01 and M02 dashboard/teachers/classes/quota/settings at 1440×900 and 390×844; also check representative dashboard/classes views at 768×1024. Confirm no horizontal overflow, clipping, collision or lost action/status labels. Save before/after evidence in FEAT-066. The shared login is checked for regression only and is not restyled.
- AC6: Manually confirm keyboard focus/activation, M01 tab arrow/Home/End semantics, minimum 44px target sizes for primary controls, static inbox and organization context, M01 decision counters, and no School Manager child-media surface.
- AC7: Do not invoke credentials, backend, production, provider, or real user/child data. Do not run automated tests/builds. Keep API-blocked flows visibly unavailable and document exact dependencies.
- AC8: Update FEAT-066 context, decisions, evidence and status after approval, implementation and manual review. Before each commit/push, run `python tools/validate_repository_security.py`, stage only approved paths, preserve unrelated modifications, and use non-force fast-forward publication only.

## Review workflow

1. Verify the authorized worktree root/branch/status and canonical SRS authority/hash.
2. Record this revision and exact plan hash in the feature-local approval ledger before product-code changes.
3. Recheck source/API flow support and write the audit matrix.
4. Implement the bounded visual refresh; use no new package/assets.
5. Check port 5173 and reuse/start only the loopback School Manager preview. Manually inspect the specified routes/viewports and save screenshots/observations.
6. Update FEAT-066 context, decisions, evidence and status; check the scoped diff and repository security validator before commit/push.
