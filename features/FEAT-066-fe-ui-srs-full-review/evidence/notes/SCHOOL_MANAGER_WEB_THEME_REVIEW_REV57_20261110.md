# FEAT-066-EV-010 — School Manager SRS flow and school-theme review

Date: 2026-11-10 (Asia/Bangkok)
Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
Branch: codex/fe-ui-web-remediation
Plan revision: 8, SHA-256 C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C
SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. This review treats §§1–31 as target requirements and §32 as environment-specific evidence only.

## Scope and result

The source-to-flow audit in EV-009 remains the detailed flow matrix. School Manager is incomplete against §21.5. This review preserves the existing compatible read/list and lesson-grant review surfaces, keeps fixture-only summaries labeled, and keeps all API-blocked operations visibly unavailable. It does not change backend, API contracts, auth policy, or business behavior.

The authenticated School Manager shell, M01 and M02 screens now use a scoped school-office visual system: warm paper/chalk surfaces, forest and leaf green accents, muted marigold/clay status colors, readable ink, clear focus, restrained borders/shadows, and responsive wrapping. The design is for adult school staff and does not add child-facing decoration or media.

## Routes and responsive evidence

Local preview at http://127.0.0.1:5173/ was reused, bound to 127.0.0.1. No credentials or backend session were used.

The final capture set contains 16 route/viewport observations and a separate M01 post-action screenshot:
- Login regression: 1440x900 and 390x844.
- M02 dashboard: 1440x900, 768x1024 and 390x844.
- M02 teachers, classes, quota and settings: each at 1440x900 and 390x844.
- M02 classes: also at 768x1024.
- M01 public review: 1440x900 and 390x844.
- M01 after local request-changes interaction: 1440x900.

All 16 observed pages have horizontalOverflow=false. All 15 disabled actions measured by the capture helper have insideViewport=true and minHeight at least 44px. The narrow views reflow the navigation and content; class tables retain their local scroll region. No title/action collision or clipped quota action was observed.

Before-review evidence is retained under screenshots/double-check/ and the existing remediation folders. The new final captures and observations are under screenshots/school-manager-theme-final/. Login appears only as regression evidence; its styling was not changed in revision 8.

## Interaction and accessibility observations

- M01 starts with tab and panel IDs connected through aria-controls and aria-labelledby; selected state, roving tabIndex and hidden panel state match.
- ArrowRight, ArrowLeft, Home and End move active tab focus/selection to the expected tab and reveal the linked panel.
- On the non-persistent local preview fixture, requesting changes updates counts to Chờ duyệt: 2, Đã duyệt: 0, Yêu cầu chỉnh sửa: 1. The UI explicitly says this local change was not sent to the API.
- Inbox is a static, non-interactive Hộp thư chưa khả dụng status with no unread dot. Organization context is a static DIV, not a dropdown.
- The narrow logout control measured 117x54px and remained inside the viewport. Keyboard activation returned to /login and cleared the local s2l web role/authenticated session keys.
- DOM semantics and keyboard behavior were reviewed in-browser; no screen-reader device/assistive-technology run was performed.

## Flow completeness and API dependencies

See the current-vs-target source matrix in SCHOOL_MANAGER_WEB_SRS_FLOW_AUDIT_REV57_20261110.md. Summary:
- Dashboard organization metrics and organization quota values are local fixtures; a Manager organization summary/quota contract is missing.
- Class list and read-only roster/profile reads have relevant GET contracts. Capacity-safe class creation is blocked because the create contract does not enforce capacity; archive/suspend lifecycle endpoints are absent.
- Low-level assignment create/revoke exists, but Manager Teacher directory/search/provisioning/selection and safe transfer/offboarding contracts are missing.
- Billing, invoice, payment, subscription, renewal, grace-period and downgrade API flows are absent. No prices or policies are inferred.
- Organization quota summary, top-up and verified payment grant APIs are absent.
- Inbox/notification route and API are absent.
- M01 lesson access-grant list/decision APIs exist. Local preview decisions remain non-persistent; the four-item review rubric remains an SRS clarification.
- School-scoped feedback listing/reply API and route are absent.
- No child story/media surface is exposed. Backend tenant/privacy enforcement was not runtime tested and requires backend contract/security evidence.

These gaps block a complete School Manager production flow. Do not claim otherwise until compatible API/contracts are provided.

## Worktree and validation limits

The active root and branch were verified as F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation and codex/fe-ui-web-remediation. The root checkout inventory had no FEAT-066-only paths missing from this worktree; no root files were copied or overwritten. Pre-existing unrelated root approval, Parent UI and FEAT-070 changes were preserved.

No tests, builds, backend calls, provider calls, production data, credentials or real user/child data were used. This evidence is a manual local visual/DOM interaction review, not authenticated end-to-end verification.
