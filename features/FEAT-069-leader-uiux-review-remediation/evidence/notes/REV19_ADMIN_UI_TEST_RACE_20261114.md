# Rev19 — Fix Flaky Async `useEffect` Race in `apps/admin-ui` CI Check (`2026-11-14`)

## 1. Root Cause Analysis

On commit `21ca31f0`, GitHub Actions reported `4 / 5` checks passing (`Repository policy checks`, `Backend unit and contract tests`, `Child UI checks`, and `Teacher UI checks` all `success`), with `Admin UI checks` (`apps/admin-ui`) failing in `src/__tests__/app.test.tsx:44`:

- **Failing assertion:** `AssertionError: expected "listClasses" to be called once, but got 0 times`
- **Mechanism:** In `AdminAccessGate` (`apps/admin-ui/src/App.tsx`), once `classService.currentAssignments()` resolves with `school_admin`, `<ClassesPage />` renders and synchronously commits `<h1>Lớp học</h1>` into the DOM. `@testing-library/react`'s `await screen.findByRole('heading', { name: 'Lớp học' })` can resolve as soon as the heading enters the DOM, before React 19's asynchronous passive `useEffect(() => { void refresh() }, [])` in `ClassesPage.tsx` runs `classService.listClasses()`. Immediately calling synchronous `expect(classService.listClasses).toHaveBeenCalledOnce()` then races with React's passive-effect scheduler turn.

## 2. Change Implemented

Under approved Plan Rev19 (`plan/PLAN_REV19_ADMIN_UI_TEST_RACE.md`, SHA-256 `9BAF0070DCDFECBB368491E04A1D4575A7D3321B7AF0CB1434F18E936383797D`):

- Updated `apps/admin-ui/src/__tests__/app.test.tsx` to import `waitFor` from `@testing-library/react`.
- Awaited `await waitFor(() => expect(classService.listClasses).toHaveBeenCalledOnce())` and `expect(await screen.findByText('BE1 chưa trả lớp nào cho tài khoản này.')).toBeTruthy()` while retaining every existing assertion unchanged.
- Made zero changes to `UI_Project/`, `backend/`, `apps/admin-ui/src/pages/`, `.github/workflows/ci.yml`, `tools/validate_*.py`, or canonical `FEAT-063` SRS `v2.5-draft`.

## 3. Verification

- `npm run check --prefix apps/admin-ui` (`tsc -b && vite build`, `oxlint`, `vitest run`): passed (`0` errors; `2/2` tests passed in `497ms`, followed by a second clean `vitest run` in `480ms`).
- All 5 repository policy validators (`validate_harness.py`, `validate_skeleton.py`, `validate_architecture.py`, `validate_repository_security.py`, `validate_team_allocation.py`) and `git diff --check` verified passing (`EXIT 0`).
