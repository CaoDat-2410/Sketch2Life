# FEAT-081 — Plan Revision 51C: Parent SVG-guide backend contract and E2E recovery

**Status:** APPROVED by the owner's direct 2026-11-21 instruction to inspect and fix backend defects as well as frontend behavior.
**Product authority:** FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev71; unsigned.
**Feature/worktree:** FEAT-081, branch `feature/fe-mobile-remediation`; real Android app on `emulator-5554`, ADB only.

## 1. Finding

The real Parent UI called `POST /api/parent/v1/ai/sketch-guides`. The route is mounted and authentication is active (unauthenticated probe returns 401). The authenticated UI request returned 404 because the selected custom subject had no matching pinned SVG guide. The backend already reports `CURATED_SVG_GUIDE_NOT_FOUND`; it does not dispatch Modal. The old `parent.sketch-guide.generate` workload is marked retired/disabled, so this amendment does not re-enable it or claim AI guide generation works.

This is an optional capability. FEAT-063 says missing catalog/capability must not block Parent capture. The observed defect is the failure path presented by the app and the lack of a focused API regression test/safe request correlation on this backend response.

## 2. Authorized scope

1. Add safe request correlation and structured, non-sensitive backend diagnostics to the Parent SVG guide route for invalid input, unavailable source and no-match outcomes. Do not log the entered topic/subject or child data. Preserve the existing typed status/code contract; no raw model/provider output.
2. Add focused backend contract tests for authentication, successful curated resolution, missing-source 404/code, and the guarantee that a missing source does not invoke Modal.
3. Update the Parent client/controller UI to explain that no matching guide is available and allow the adult to continue to mandatory capture without a guide. Keep catalog guide rendering unchanged.
4. Resume the same real Parent E2E at the current UI state; no extra account/profile/run. Continue testing backend APIs and Modal workloads in the approved one-inference-per-workload limits. Do not bypass APIs or use fixture/preview mode.
5. Record API status, safe request/correlation IDs, duration, stage and blocker in this feature's evidence, then update CONTEXT.md and status/STATUS.md.

## 3. Limits

- No reactivation or dispatch of the retired `parent.sketch-guide.generate` worker; no FLUX; no new Modal workload/deploy/warm/stop for this amendment.
- No database migration/reset/reseed, seed/account cleanup beyond Addendum 81's exact-own-account boundary, quota/payment operation, consent fabrication, real child data, secret/.env/SRS edits, commit or push.
- Do not alter activity/story/video rules. Keep Addendum 81's existing per-workload and one-candidate limits; story review remains a hard gate before video.
- If a different Parent API needs code changes outside the paths below, record its evidence and add a separate append-only approval amendment before editing it.

## 4. Acceptance

- Authenticated missing-guide request returns the documented 404 `CURATED_SVG_GUIDE_NOT_FOUND` with a safe correlation ID; no Modal call occurs.
- Backend tests pass for the focused route contract.
- UI displays a clear optional-guide-unavailable state and provides a working continue-without-guide action to the required capture step.
- Real E2E resumes without a duplicate account/profile/run; later stages are reported accurately, including any backend/API failure.
- No unrelated staged/unstaged work is reset or committed.

## 5. Allowed files

- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/application/services/parent_svg_guide.py` only if required for the typed missing-source result
- `backend/tests/contract/test_parent_svg_guide_api.py`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/screens/IdeaScreen.tsx`
- focused new mobile tests under `apps/ui-mobile/tests/`
- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`

No other paths are authorized by this amendment.
