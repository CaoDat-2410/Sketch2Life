# FEAT-066 — Full FE review against canonical SRS Rev57

Owner: User-requested read-only review. Review date: 2026-11-10, Asia/Bangkok.

## Authority and baseline

- Current product authority: `docs/context/SRS_AUTHORITY.md` and `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57 dated 2026-11-09, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`.
- Approval state: draft, awaiting formal owner sign-off. This is the current working baseline, not a signed final SRS.
- Source worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`, based at commit `95433b3a9bef893a671df6623476784dbd0fd83d` when the worktree was created.
- The FE worktree's local `docs/context/SRS_AUTHORITY.md` still says v2.5-draft. It is stale relative to the canonical root authority and must not determine current requirements.
- Existing 37-screen screenshot archive is historical synthetic-preview evidence captured on an earlier commit. It does not prove current route coverage or current tablet behavior.

## Review scope

The earlier revision 1 source review covered Parent Android and `apps/ui-mobile` as context/reference, Parent Web, Teacher UI, School Manager UI, Platform Admin UI, the additional Admin UI surface, and shared authentication/API integration. The current plan revision 3 narrows all new work to `apps/school-manager-ui`: local fixture-only preview and visual/UI/UX review of its School Manager routes. Do not inspect or run Parent mobile as part of this clarified task. Teacher, Platform Admin, and the additional Admin UI are outside the current scope.

## Existing findings and open questions

The source review in `evidence/notes/FE_UI_FULL_SRS_REVIEW_REV57_20261110.md` records confirmed gaps in Teacher run/Sketch Deck integration, School Manager organization/billing coverage, Platform Admin backend mode, manual Teacher child selection, consent-state presentation, upload recovery, and manager notification behavior. It also records Parent-specific source findings and implementation risks; those are retained as earlier evidence and are not newly runtime-verified by plan revision 2.

Open questions remain: Q-01 child eligibility/consent/exclusion/reselection/no-eligible behavior and selection evidence; §31.10 Parent no-preset activity-catalog behavior; and Parent Web scope/account-creation requirements. Do not resolve these from UI appearance alone.

## Current milestone

Plan revision 3 review is complete for School Manager source and local loopback Vite preview. The focused findings and route/screenshot coverage are recorded in `evidence/notes/SCHOOL_MANAGER_WEB_UX_REVIEW_REV57_20261110.md`; the earlier broad source note remains historical evidence and does not broaden this review. Parent mobile and every other portal remain out of scope. This was an audit only; no product code changed, and remediation is still a separate task.

## Revision 4 — School Manager web remediation (2026-11-10)

The user directly authorized implementation limited to `apps/school-manager-ui` and FEAT-066 governance/evidence in the designated `codex/fe-ui-web-remediation` worktree. Plan revision 4 is approved; see `plan/PLAN.md` and `approvals/TASK_APPROVAL.md` (plan SHA-256 `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`). This supersedes the revision 3 audit-only implementation restriction. Canonical SRS remains FEAT-063 v2.7-draft Rev57, unsigned, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; §32 remains as-built evidence only.

Initial contract audit: Lesson Library supports School Manager public-grant review; BE1 supports class list/create, adult assignment create/revoke, and consent-filtered profile-list reads. The class-create contract has no capacity input/guard, and the checked contracts expose no class archive/suspend, teacher directory, School Manager billing/invoice/payment/subscription, organization quota summary/top-up, inbox, or school feedback-reply flow. A read-only roster view may use the existing profile-list API; do not expose media or use real child data. Unsupported end-to-end flows must be visibly unavailable and documented rather than simulated. Before implementation started, no product source had been changed.
## Revision 4 implementation and review results

- M01 local preview now tracks approval and change requests independently; after requesting changes the reviewed item is removed from the pending queue, `Đã duyệt` remains 0, and `Yêu cầu chỉnh sửa` becomes 1. Preview notices state that the decision is local and is not sent to the API.
- M01 tabs have linked tab/panel IDs, selected state, roving tab focus, and Left/Right/Home/End keyboard navigation. The content panel and diff panel expose `tabpanel` semantics.
- The notification bell/unread indicator is replaced by a static unavailable status because the checked contracts contain no inbox API. The organization label is static context with no dropdown arrow.
- M02 fixture actions that implied class creation, Teacher invitation, quota purchase, parent-group sync, or subscription changes are disabled and labelled unavailable. API-backed class listing remains; a read-only roster panel uses the existing profiles endpoint and displays names only. Child media/story are not requested or shown.
- Class capacity-safe creation, archive/suspend, Teacher selection, billing/invoice/payment, subscription, organization quota, inbox, and School Manager feedback reply remain blocked on APIs/contracts recorded in EV-003. Commercial values and policy remain open in the unsigned SRS.
- Manual local UI review was captured at 1440x900 and 390x844 for login, M01, and M02 dashboard/teachers/classes/quota/settings. See EV-004 and `evidence/screenshots/remediation-after/`. No backend, provider, production data, credentials, tests, or builds were used.