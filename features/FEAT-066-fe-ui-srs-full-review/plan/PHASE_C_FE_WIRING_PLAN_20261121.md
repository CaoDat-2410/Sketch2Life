# Goal v3 Phase C web wiring plan (Teacher, School Manager)

Date: 2026-11-21. Status: plan written before implementation; execute under the existing goal v3 program approval. `approvals/TASK_APPROVAL.md` and `DECISIONS.md` are out of scope and will not be edited.

Base: worktree branch `claude/phase-c-web-wiring-f934d5`, cut from web branch tip `7a8b5729`. Only `apps/web/**`, this plan, the Phase C evidence note, `SUMMARY.md`, and `REVIEW.md` are writable for this task. Backend, Android, Platform Admin, shared UI primitives, global theme CSS, and all other worktrees are read-only.

Authority: `docs/context/SRS_AUTHORITY.md` names the local FEAT-063 v2.7-draft SRS (SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`) as the canonical working copy. The prompt cites the separate v3 worktree copy (SHA-256 prefix `443A3CA3`). This plan uses the local authority copy and its cited lines; the draft remains unsigned. Backend contract sources are read-only at BE integration commit `258ff4c00f2babb941238c088af556981ec39ae7`.

## Scope and contract

Wire goal v3 Phase C T-8a notifications and T-10d private lesson sharing into Teacher and School Manager web code. Both roles use the same authenticated `window.sketch2lifeAuth` bridge. Notification commands act only on the caller's own inbox; the client sends no role, recipient, or organization.

| Task | Route / client contract | Success | Errors / behavior |
|---|---|---|---|
| T-8a list | `GET /v1/notifications?limit=25&cursor=...`; limit 1–100, cursor opaque and passed unchanged | `NotificationPageV1`, newest first; server hides expired items; unread count capped at 100 | 400 invalid request, 401, and uniform 404; display `99+` for count 100 |
| T-8a mark one | `POST /v1/notifications/{encoded inbox_item_id}/read`, `Idempotency-Key`, no body | `NotificationV1` | 400 invalid request/key, 401, uniform 404; same key only for retry of the same action |
| T-8a mark all | `POST /v1/notifications/read-all`, `Idempotency-Key`, no body | `NotificationReadAllV1`; after success replace current list with a fresh first page | 400 invalid request/key, 401, uniform 404; a replay preserves the first result |
| T-10d private share | `POST /api/lesson-library/v1/organizations/{org}/lessons/{lesson}/access-grants`; audience `ORGANIZATION`, `PRINCIPAL`, or `PARENT_GROUP`, required `audience_ref`; keyed JSON body and no `If-Match` | `LessonAccessGrantV1`; any review state may be privately shared | Keep shared envelope copy, add uniform 404, group-state 409 and validation 422 copy; do not special-case `PUBLICATION_REQUIRED` |

Notification `safe_parameters` are data for future template resolution only. No raw value is rendered or used to construct a link. The template registry starts empty and returns a neutral title for unknown type/version. Inbox items render only template-resolved copy and timestamps. `unread_count=100` displays as `99+`.

## Files

New implementation:

- `apps/web/src/shared/api/notificationsApi.ts`
- `apps/web/src/shared/notifications/useInbox.ts`
- `apps/web/src/shared/notifications/notificationTemplates.ts`
- `apps/web/src/shared/notifications/InboxPage.tsx`
- `apps/web/src/shared/api/lessonSharingApi.ts`
- `apps/web/src/shared/api/lessonShareGate.ts`

New mocked tests:

- `apps/web/src/shared/api/__tests__/notificationsApi.test.ts`
- `apps/web/src/shared/notifications/__tests__/InboxPage.test.tsx`
- `apps/web/src/shared/notifications/__tests__/notificationTemplates.test.ts`
- `apps/web/src/shared/api/__tests__/lessonSharingApi.test.ts`
- `apps/web/src/shared/api/__tests__/lessonShareGate.test.ts`
- `apps/web/src/shared/notifications/__tests__/inboxRouting.test.tsx` (one Teacher and one School Manager route case)

Minimal existing-file edits only:

- `apps/web/src/modules/teacher/App.tsx`: import `InboxPage`; render it for `/teacher/t10-inbox`.
- `apps/web/src/modules/school-manager/be1/App.tsx`: import `InboxPage`; add `/school/inbox` before the generic unavailable route; remove its obsolete `UNAVAILABLE.inbox` entry.
- `apps/web/src/shared/navigation/WebAppShell.tsx`: change the two inbox navigation states to `available`; no badge.
- `apps/web/src/modules/school-manager/be1/__tests__/app.test.tsx`: remove `/school/inbox` from the obsolete unavailable-route case so it continues to test only unavailable pages.

No edit to `backendApi.tsx`, `TeacherApiLessonPage.tsx`, `TeacherOccurrencePage.tsx`, shared UI primitives, Platform Admin, global CSS, backend, Android, approval records, or decisions.

## UI states and behavior

- Loading uses status semantics and `aria-busy`; empty copy says only that the inbox is empty.
- Initial error uses the shared API message and retry action except for uniform 404, which has no retry action. Failed refresh retains any previously loaded list.
- Ready list distinguishes unread items with the visible text label `Chưa đọc`; read items show `read_at` and no mark-read control. Mark-one and mark-all controls are disabled while a command is busy; mark-all is also disabled when unread count is zero. Load more appears only with a cursor, is user-triggered, and stops on a repeated cursor.
- All result/error messages are in an `aria-live="polite"` region; controls remain keyboard reachable. Render dates with `Intl.DateTimeFormat("vi-VN")` in the user's time zone. Do not render `safe_parameters` and do not use `dangerouslySetInnerHTML`.
- One key is kept per pending user action until success or definite rejection; network/ambiguous failures reuse it for the same retry. Prevent concurrent/double command dispatch. Ignore superseded or unmounted requests; append pages with id deduplication. Mark-one patches the returned item, decrements counts below 100 only, and leaves a capped count at 100 until reload. Mark-all reloads and replaces the first page.
- Private sharing uses the actual `TeacherLessonDetail` fields: deny archived lessons and missing `current_version`; allow otherwise without reading `review_state`. Only a PUBLIC audience needs a School Manager decision (SRS FR-PL-05 l.2646, FR-PL-06 l.2647, BR-51 l.2676).

The shared UI package has no imports in existing Teacher or School Manager pages. `tailwind-utilities.css` is imported by the Teacher AI workflow page, but it is not a global portal import and is absent from School Manager. The new inbox therefore uses existing `tw-*`/`s2l-*` portal classes within `InboxPage`; no shared style or Tailwind import will be added.

## Error copy and SRS basis

| Case | UI handling | SRS basis |
|---|---|---|
| Cursor page defaults to 25, max 100; cursor remains opaque | API query and append behavior | l.1640 |
| Inbox item contains no child media/story and is resolved by type/version | render only registered template text; never raw `safe_parameters` | l.1681, FR-B-09 l.595 |
| `unread_count=100` represents 100 or more | show `99+` | backend schema contract; SRS l.1681 establishes inbox read, no exact badge wording |
| Wrong scope and missing item share one 404 shape | fixed Vietnamese message; no retry control for the initial 404 state | l.864–865 |
| State-changing command replay | visible-ASCII key, reused only for identical action retry | l.1697 |
| Public lesson approval and private audience sharing | no private `APPROVED` gate; PUBLIC workflow stays separate | FR-PL-05 l.2646, FR-PL-06 l.2647, BR-51 l.2676 |
| Custom 404, group-inactive 409, and expiry/self-share 422 Vietnamese wording | safe fixed copy; wording is a client choice | no literal SRS wording |

T-8a has no producer types today. Template-specific text will be added only when a producer has an SRS-sourced type/version. The shell unread badge and private-share dialog remain follow-ups; no Parent/group picker data source exists in web.

## Out of scope, constraints, and expected conflicts

- T-13a Teacher run cancel/delete and T-4a1 wait for Phase D because no Teacher run screen exists; Android; backend; Platform Admin pages; capacity/subscription/quota/billing/payment; public share UI; share dialog; shell unread badge; producers and notification-specific text.
- Keep the occurrence pin `APPROVED` checks and message unchanged. D8 / Q-3 from the T-10d evidence reserves the occurrence-pin question for a separate decision; private sharing is a different capability.
- Expected sibling restyle conflict candidates: Teacher `App.tsx`, School Manager `App.tsx`, and `WebAppShell.tsx`. Keep edits to the exact routing/navigation hook-up above; no formatting or styling churn.
- Existing observed code facts: no private-share screen/call exists; `requestPublicReview` is the only grant creation client call and uses `PUBLIC`; no web mapping for `PUBLICATION_REQUIRED` exists; `APPROVED` checks in `TeacherOccurrencePage.tsx` remain untouched.

## Acceptance criteria

1. API clients follow the checked backend contracts, validate keys and response contract literals, safely map errors, encode IDs, and never log credentials, bodies, IDs, or notification parameters.
2. The inbox renders the required loading, empty, error, unread/read, mark, capped-count, timestamp, pagination, accessible-message, and unmount/stale-response behaviors without displaying raw notification parameters.
3. Both role routes render the shared inbox; the two shell items are available without a badge; Platform Admin remains unchanged.
4. Private-share client accepts only private audiences with required references, sends no `If-Match`, never gives `PUBLICATION_REQUIRED` special handling, and the gate never reads `review_state`; PUBLIC review and occurrence-pin behavior remain unchanged.
5. Mocked tests cover the requested API, UI, route, retry, deduplication, audience, and gate cases. In `apps/web`, `npm run check` passes with 0 build errors, 0 new lint warnings over the baseline of 31, and all 308 baseline tests passing plus the new tests. `python tools/validate_repository_security.py` and `git diff --check` pass.
6. Write `SUMMARY.md` and `REVIEW.md`, perform strict diff review and fix findings, then write the feature evidence note last with exact test/check counts, environment, results, limitations, and follow-ups. Do not commit or perform Git writes.
