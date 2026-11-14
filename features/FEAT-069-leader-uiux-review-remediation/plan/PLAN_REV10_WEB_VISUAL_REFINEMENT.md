# Plan Rev10 — polish operations review screens

**Feature:** FEAT-069 — Leader review UI/UX remediation
**Date:** 2026-11-14 (Asia/Saigon)
**Status:** APPROVED under the owner's direct request to improve the UI and UX shown in the supplied screenshots.
**Target branch:** `FE_UI_Project_Ver2`

## Context

The owner reports that current role web UI looks poor despite flow review. Three supplied screenshots show the Platform Admin Activity Catalog form rendering as inline/raw fields, the Admin quota/reconciliation queue needing stronger hierarchy, and the School Manager publication queue/detail appearing as unstyled browser buttons and crowded content. This plan targets those shown surfaces and their responsive layouts.

The primary application lives under `UI_Project/`. Parent is the Android WebView experience; the screenshots here concern Platform Admin and School Manager web workspaces. The owner asked to keep all content as mock preview and previously authorized publishing UI work normally to `origin/FE_UI_Project_Ver2` when fast-forwardable.

## Authority and references

- Current product requirement authority: `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.5-draft, still unsigned.
- Current implementation evidence: `UI_Project/shared/roleFlows.tsx`, `UI_Project/shared/roleFlows.css`, and the shared role shell.
- Leader visual reference: Rev38 A02 Platform Admin operations and M01 School Manager publication review boards, plus shared UI01 component tokens. Rev38 is generated proposal material, not a signed contract.
- Use the existing calm blue primary, mint support and neutral surfaces. Preserve role identity and all existing review steps, counts and local-only boundaries.
- The separate `UI_Project/parent-android/apps/ui-mobile` legacy Expo experience is not part of these screenshot pages or the Parent APK entry point and is not to be changed.

## Goal and scope

Make the three screenshot surfaces feel deliberately designed, readable and easy to operate without changing the business flow or implying a real API operation:

1. Platform Admin `catalog`: style the draft composer, controls, status filters, version list and selected-version detail; place list and detail in a clear desktop hierarchy and stack them cleanly on narrow viewports.
2. Platform Admin `billing-ops`: refine operational status cards so invoice/callback state, detail and boundary are easy to scan and open, including empty-search behavior.
3. School Manager `review`: style the pending queue, selected lesson/version header, visibility distinction, content cards/tabs, four review gates, disabled/enabled decision controls, revision request and local result/next-item state.
4. Add restrained hover/focus/disabled states, spacing, typography and status badges using code-native styles. Do not add generated images or external assets.

## Acceptance criteria

- **AC1 — no raw browser controls:** Catalog labels, inputs, select, textareas, queue rows, tabs and buttons use consistent project styling and do not overlap or fall back to default controls.
- **AC2 — clear hierarchy:** Each screen has a clear page title, preview boundary, section grouping, item identity/version, status, and primary/secondary action hierarchy.
- **AC3 — business-flow preservation:** All sample values/statuses and actions remain local fixtures; Manager approval remains disabled until all four gates are checked; no API/auth/network/persistence or new behavior is introduced.
- **AC4 — accessible interaction:** Keyboard focus is visible; clickable rows and tabs have readable selected/disabled states; text remains legible and content avoids horizontal clipping at desktop and narrow widths.
- **AC5 — verification:** Build all five `UI_Project` web workspaces and manually review the three affected routes in the local browser at desktop and narrow layout. Do not run automated tests.
- **AC6 — governance/security:** Update the feature context, decision, approval, evidence, status and source register. Run `git diff --check` and `python tools/validate_repository_security.py` before commit and immediately before each push. Push only as a normal fast-forward.

## Exclusions

No SRS, API, auth, backend, schema, data contract, workflow order, business state, live data, payment, upload, AI/ASR, or persistence changes. No external hosting deployment. No changes to Parent, Teacher, other Manager/Admin routes beyond shared style regressions if discovered, legacy Expo, or top-level legacy `apps/`. No generated raster assets or automated tests.
