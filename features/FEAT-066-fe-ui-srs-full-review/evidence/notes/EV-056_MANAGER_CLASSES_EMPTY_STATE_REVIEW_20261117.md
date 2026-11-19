# FEAT-066 EV-056 — School Manager Classes screen review

- Date: 2026-11-17 (Asia/Bangkok).
- Plan: plan/PLAN_REV50_MANAGER_CLASSES_EMPTY_STATE_REVIEW_20261117.md.
- Approval: FEAT-066 Revision 50 in approvals/TASK_APPROVAL.md.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 through docs/context/SRS_AUTHORITY.md; unsigned.
- Review basis: owner screenshot, ClassesPage/service/CSS, SRS FR-T-02/FR-T-03, and one authenticated read-only QA API request.

## Runtime and SRS

- Firebase QA Manager sign-in: 200.
- GET /api/be1/v1/organizations/{organization_id}/classes: 200 with zero items. The screenshot is a valid empty organization state, not an API/network failure.
- FR-T-02 expects authorized School Managers to create classes within capacity, manage roster and assign one responsible Teacher.
- FR-T-03 requires 10 included class slots plus purchased slots and a backend guard against concurrent creation above effective capacity.
- The UI blocks class creation because BE1 does not yet enforce capacity. This is fail-closed and appropriate for the current API, but the target Manager workflow is incomplete until BE capacity enforcement is available.
- The current grid stacks below 620px. No class was created; no database row changed.

## Findings

1. Confirmed API-failure UX bug: when listClasses rejects, ClassesPage clears classes and renders both the error alert and the normal empty state. The screenshot is not in this error state because the live GET returned 200.
2. The empty copy “BE1 chưa trả lớp nào” can imply backend failure although the successful response was empty. Suggested copy: “Tổ chức hiện chưa có lớp học nào.”
3. The detail panel asks the user to select a class, then shows missing capacity/Teacher/archive capabilities even when there is no selected class. Prefer one concise no-class state; show limitations with actual class details.
4. The capacity notice is truthful but uses the visual weight of an error. Neutral info styling would distinguish an unavailable capability from a failed request. Keep creation disabled until BE1 enforces FR-T-03.

## Scope

Review only: no source/CSS change, app test suite or build. Browser form interaction was not automated. No commit or push.
