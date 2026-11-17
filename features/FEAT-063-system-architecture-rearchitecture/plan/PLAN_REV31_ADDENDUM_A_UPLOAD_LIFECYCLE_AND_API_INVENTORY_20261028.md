# Plan Rev31 Addendum A - upload lifecycle and API inventory

- Feature: FEAT-063.
- Status: owner-authorized implementation scope, recorded as an addendum to approved Plan Rev31.
- Authority: the owner's direct instruction to proceed, list every existing API after implementation, and adapt older APIs where needed for FEAT-063.
- Parent plan: `PLAN_REV31_LESSON_LIBRARY_API_IMPLEMENTATION_AND_INVENTORY_20261028.md`.

## Scope delta

1. Add owner-scoped `GET /api/lesson-library/v1/upload-sessions/{upload_session_id}` so a client can resume an interrupted chunked upload by reading its accepted part numbers and expiry.
2. Add owner-scoped `DELETE /api/lesson-library/v1/upload-sessions/{upload_session_id}` so an open upload can be safely aborted and its private chunks deleted. Repeating an abort returns the terminal session state.
3. Reconcile `POST /upload-sessions/{upload_session_id}/complete` to the synchronous scanner/parser implementation: return `200 LessonSourceDocumentStatusV1` with `READY_FOR_REVIEW`, not `202 EXTRACTING`.
4. Keep the lesson visibility projection aligned with active, unexpired Public, selected-audience and organization grants, including grant acceptance/revocation.
5. Record all 135 current router declarations and composition status. The two new operations increase the original Rev29 contract from 28 to 30 operations.

## Acceptance criteria

- A verified upload owner can inspect and abort only their own upload session.
- Lesson source completion reports its synchronous scan/extraction result; no queue or AI behavior is implied.
- Public approval and grant revocation recompute lesson visibility without removing access provided by another active grant.
- The API inventory distinguishes 121 unconditional combined-app routes, 3 conditional local-storage routes, and 11 candidate/unmounted declarations; framework-generated docs routes are noted separately.
- Existing Parent, Teacher, BE1 and demo route paths remain unchanged unless the inventory finds a concrete incompatibility.
- No tests, builds, Docker actions, database access/migrations, security validator, credentials, AWS calls, deployment, commit or push are performed.

