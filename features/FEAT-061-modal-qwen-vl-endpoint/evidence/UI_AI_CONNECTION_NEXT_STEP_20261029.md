# Read-only next-step check: active UI versus tested demo

- Date: 2026-10-29, Asia/Saigon.
- Source: dev-based worktree at `529cbef9`.
- Trigger: the owner asked what to do after completing the bounded backend smoke and the Claude handoff.
- Execution: source inspection only; no install, UI/backend startup, cloud/model call, source change, merge or publication.

## Observed source boundaries

- Root `package.json` includes `apps/child-ui`, `apps/teacher-ui` and `apps/admin-ui` in the `check:active-ui` scripts.
- `apps/ui-mobile/App.tsx` exports `BaoApp`. Its `src/context/AppContext.tsx` creates `createDemoApi()` and uses `uploadImage` / `runUnderstanding`. `src/demo/api.ts` uses `EXPO_PUBLIC_API_URL` and the `/v1/sessions/...` demo workflow. This is the backend workflow verified by the completed Modal smoke.
- `apps/child-ui/src/services/apiClient.ts` instead reads `EXPO_PUBLIC_BE1_BASE_URL`, calls `/api/be1/v1${path}`, and supports BE1 device/grant headers. This is a different API and authentication boundary from the tested demo.
- Child UI has fixtures, but its API client contains real HTTP fetch logic. Fixture presence alone does not establish that the whole app is mocked or that no AI integration exists.
- Node dependencies are absent in the new worktree at inspection time. No package installation or frontend execution was performed.

## Recommended first next task — not implemented

Trace the active child UI image/drawing action through its BE1 route, service/port and any downstream AI/BE2 adapter. Identify what already exists and which connection, if any, is missing. Do not assume the whole bridge is absent merely because the client does not use the demo routes.

The completed demo smoke does not prove the active child UI can reach Qwen. Changing a frontend base URL to the demo backend is not evidence that its BE1 routes/device-grant workflow are supported there.

Keep this first task read-only. Present the actual path and gaps before proposing source changes or a newly bounded synthetic UI/model test. Any new implementation needs the applicable plan/authorization; preserve the protected original FEAT-061 records and existing provider/contract/production boundaries. The old probe's one-request budget remains consumed.

Both tested processes remain stopped at the last confirmed checkpoint. No mobile result or new execution permission follows from this recommendation.
