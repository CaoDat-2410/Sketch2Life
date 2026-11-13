# FEAT-069 Plan Rev3 addendum — Parent Lesson Library API

- **Status:** APPROVED by the project owner for this exact additive frontend scope.
- **Date:** 2026-11-14 (Asia/Saigon).
- **Parent plan:** `plan/PLAN_REV3.md` (SHA-256 `21A1FB640990D078793918AFCA651394FBACB42BFD0F80C173B28A385BFCAEB9`).

## Additive scope

Wire the Parent mobile library to the current delivery branch's mounted Lesson Library endpoints when `window.sketch2lifeAuth.getIdToken` is present:

- Read public/shared lessons and invitation list with the existing typed client methods.
- Read a selected lesson's detail on user demand with the existing typed client method.
- Submit invitation accept/decline only after an explicit user button press, through the existing typed, idempotent client method. Show the returned action outcome and refresh the relevant reads.
- Preserve a visibly labeled fixture preview without auth. In connected mode, show loading/error/unavailable states and never silently substitute fixture lessons when an API request fails.
- Keep Parent profile/story/photo/ASR/AI/video/playback and unsupported run behavior preview-only. Make no request to those routes.

## Acceptance criteria

- **AC11:** Parent library reads use only mounted `GET /api/lesson-library/v1/me/lessons`, `GET /me/lesson-invitations`, and `GET /me/lessons/{lesson_id}` routes, with the typed client and auth bridge. API results map only fields present in the contract; unavailable teacher/organization display names are not invented.
- **AC12:** Accept/decline buttons call the existing typed invitation response operation only when the user selects one; completion/error is surfaced and current reads are refreshed. No such API action occurs during implementation/build/review.
- **AC13:** No-auth mode remains a labeled sample preview; connected-mode failures do not reveal fixture rows as API results. All other Parent profile/story/AI/media flows remain explicitly preview-only.

## Exclusions

Backend/API/auth/schema/SRS changes, live API/auth/database requests during implementation or QA, any profile/story/ASR/AI/video route call, generated/real child data, parent-group/child-profile operations, new branch source, and automated tests.

## Approval basis

The owner directly requested building the complete UI against APIs currently present in the GitHub project and satisfying the leader's review. This addendum narrows that instruction to the mounted Parent Lesson Library contract. It does not authorize backend changes or claim the delivery branch's missing auth runtime is available.
