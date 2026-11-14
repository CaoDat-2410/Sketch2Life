# Plan Rev19 — Fix Flaky Async `useEffect` Race in `apps/admin-ui` CI Check (`4/5` -> `5/5`)

- **Feature:** `FEAT-069-leader-uiux-review-remediation`
- **Status:** READY FOR OWNER APPROVAL (`DRAFT` -> `APPROVED`)
- **Date:** 2026-11-14 (Asia/Saigon)
- **Trigger:** Project owner uploaded GitHub Actions `4/5` check failure screenshot on commit `21ca31f0` (`"nó báo lỗi nè"`). Inspection of GitHub Actions check-run `132472499432` (`Admin UI checks`) showed failure in `apps/admin-ui/src/__tests__/app.test.tsx:44` (`AssertionError: expected "listClasses" to be called once, but got 0 times`), while `Repository policy checks`, `Backend unit and contract tests`, `Child UI checks`, and `Teacher UI checks` all passed (`success`). Locally running `npm run check --prefix apps/admin-ui` passed `2/2`, confirming a React 19 passive `useEffect` timing race between synchronous DOM commit of `<h1>Lớp học</h1>` and `ClassesPage` calling `classService.listClasses()`.

## Scope & Strict Boundaries

1. **Await `listClasses()` passive effect deterministically in `apps/admin-ui/src/__tests__/app.test.tsx`:**
   - Import `waitFor` from `@testing-library/react`.
   - Keep all existing assertions (`findByRole('heading', { name: 'Lớp học' })`, `login`, `currentAssignments().toHaveBeenCalledOnce()`).
   - Wrap `expect(classService.listClasses).toHaveBeenCalledOnce()` in `await waitFor(...)` and wait for the settled empty state (`await screen.findByText('BE1 chưa trả lớp nào cho tài khoản này.')`) so `ClassesPage`'s `useEffect` (`refresh()`) reliably invokes `listClasses()` and finishes its `setLoading(false)` transition before test cleanup.
2. **Governance & Security Updates:**
   - Record Rev19 evidence, decision, context, and status under `features/FEAT-069-leader-uiux-review-remediation/`.
3. **Exclusions:**
   - Do **not** relax any test assertion, delete tests, or mock away application logic.
   - Do **not** modify `UI_Project/`, `backend/`, `apps/child-ui/`, `apps/teacher-ui/`, `apps/admin-ui/src/pages/`, `.github/workflows/ci.yml`, `tools/validate_*.py`, or canonical `FEAT-063` SRS `v2.5-draft`.
   - Remember not to commit `apps/admin-ui/node_modules/` (gitignored).

## Acceptance Criteria

- **AC19.1:** `apps/admin-ui/src/__tests__/app.test.tsx` awaits `classService.listClasses` deterministically without relaxing any existing assertion.
- **AC19.2:** `npm run check --prefix apps/admin-ui` (`tsc -b && vite build && oxlint && vitest run`) passes locally across repeated runs (`0` errors).
- **AC19.3:** `git diff --check` and all 5 `python tools/validate_*.py` scripts exit `0`.
- **AC19.4:** Normal fast-forward commit & push to `origin/FE_UI_Project_Ver2` achieves `5/5` green checks on GitHub Actions (`Repository policy checks`, `Backend unit and contract tests`, `Child UI checks`, `Teacher UI checks`, `Admin UI checks`).
