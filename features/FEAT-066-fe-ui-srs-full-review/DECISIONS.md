# FEAT-066 decisions

## D-066-01 — Use Rev57 as the sole product baseline

Use FEAT-063 SRS v2.7-draft Rev57 from the root authority record for this review. The FE worktree's v2.5 authority copy is stale and does not override it. The Rev57 draft remains unsigned; report its approval status accurately.

## D-066-02 — Separate target products from references and legacy surfaces

For the current plan revision 3, audit only `apps/school-manager-ui`. Do not inspect or run `apps/mobile`, `apps/parent-ui`, or `apps/ui-mobile`; do not expand to Teacher, Platform Admin, or the additional Admin UI. The earlier revision 1 review remains historical evidence and does not broaden the current task.

## D-066-03 — Review only; remediation requires separate approval

This task records findings and evidence only. No product source, tests, build artifacts, backend, credentials, or runtime data are changed or invoked.

## D-066-04 — Keep engineering risks separate from SRS gaps

Record local port overlap, missing portal test files, and preview-only behavior as implementation/validation risks, not as product requirements inferred from the SRS.

## D-066-05 — Local visual audit uses isolated fixture previews

Start only the School Manager local Vite preview, bound to loopback, and use fixture/preview states. Do not start Parent mobile, backend or provider services, invoke external APIs, or supply credentials. If a screen cannot be reached without those dependencies, stop at source review and record the limitation.

## D-066-06 — Responsive checks are exploratory outside desktop support targets

Review the target web portals at desktop sizes required by the SRS and at a narrow viewport to find layout/accessibility defects. Report narrow-viewport issues as UX robustness findings unless the SRS explicitly makes the behavior a support requirement.

## D-066-07 — Treat preview findings as UI evidence only

The School Manager local preview uses synthetic, non-persistent state. Use it to confirm visible layout and preview interaction behavior only; do not treat preview values or toast messages as evidence of backend persistence, billing state, or production workflow completion. Report backend capabilities from source inspection and preserve any SRS policy questions as open.

## D-066-08 — Direct approval for School Manager web remediation

On 2026-11-10 the user approved plan revision 4 for School Manager web only, limited to `apps/school-manager-ui` and FEAT-066 governance/evidence in `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` on `codex/fe-ui-web-remediation`. This supersedes D-066-03's remediation-excluded scope for this bounded task. Parent mobile and all other portals remain out of scope. The approval record includes the verified plan SHA-256 before code changes.

## D-066-09 — API-compatible work only; missing capabilities stay unavailable

Use existing versioned APIs/contracts where they support the complete required operation. Do not treat a partial endpoint as support for a broader business flow: the existing class create endpoint does not enforce SRS class capacity, assignment writes have no teacher directory/selection contract, and roster profile reads do not establish full roster lifecycle management. Billing, payments, subscription, organization quota, notification inbox and School Manager feedback-reply flows have no compatible endpoint in the checked API surface. Show unsupported actions as unavailable and record backend/API dependencies; do not create local success states or transactions. Preserve School Manager's child-media deny boundary.
## D-066-10 — Record post-implementation review against the authorized FE-only scope

The implementation uses only compatible existing FE/API behavior and visibly marks unsupported organization flows unavailable. Local preview fixture state is explicitly labeled and does not claim persistence; no class creation, quota purchase, subscription, Teacher assignment, inbox, or feedback-reply success is simulated. The after-review evidence is captured at desktop 1440x900 and narrow 390x844 in EV-004. M01 keyboard review confirmed ArrowRight moves focus/selection to the second tab and exposes its linked panel. No production/backend session was used.
## D-066-11 — Reuse the existing logout callback for School Manager

Expose a visible, keyboard-accessible logout action on authenticated M01/M02 pages and call the existing `TeacherContext.logout` callback. Do not create a second session-clear path, new auth policy, backend endpoint, or provider behavior. Treat the missing control as a user-reported FE usability follow-up, not as a newly inferred SRS requirement. Verify desktop and 390px layout plus session clearing and redirect to `/login`.
Revision 5 verification: the shared logout action passed the four local dashboard/settings × desktop/narrow interactions. Enter returned to `/login`, both existing web session keys were absent, and direct protected-route navigation stayed at login. Evidence is recorded under FEAT-066-EV-005. The optional Firebase sign-out bridge was not configured in the local preview.

## D-066-12 — Trace School Manager UI test flows to canonical SRS and actual contracts

The sequential flow guide covers the School Manager screens in SRS §21.5 and related use cases/requirements. For each flow, distinguish target behavior, current FE route/state, source-checked API support, and missing dependencies. Treat local fixtures as visual/interaction evidence only, retain open SRS policy questions, and do not infer requirements from §32 or simulate unavailable backend operations. See FEAT-066-EV-006.
