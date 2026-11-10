# FEAT-071 — Parent child-profile quick switch

- Status: IMPLEMENTED; manual local FE walkthrough completed.
- Active worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Runtime: http://127.0.0.1:5171.
- Product authority: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; pending formal owner sign-off.

## Diagnosis

- P13 profile rows looked like a selector but opened /p10-child-profiles/:childId; only the detail page changed selectedProfileId.
- The detail action said Chọn mặc định, although selectedProfileId is session-local React state and resets to child-minh after a reload.
- P01 already switches the same selected profile with one tap.
- Source inspection found that /p10-child-profiles is currently a redirect to /p13-settings#child-profiles in App.tsx. P10ChildProfilesPage exists in source but is not mounted as a separate route. /p10-child-profiles/:childId is the active profile-detail route.

## Implemented behavior

- Selecting an active, non-archived row on P13 updates the shared selectedProfileId immediately and keeps the user on P13.
- Profile details have a separate, labeled action; the detail page uses Đang dùng and Dùng hồ sơ này wording.
- Archived and non-active rows are disabled for selection, while the details/restore action stays available.
- The dormant P10 list component shares the same row implementation for consistency; its route remains the existing redirect.
- Selection stays in the current Parent UI session. This change does not add API calls, storage, billing changes, or account switching.

## SRS constraints

The SRS requires a Parent to choose a child profile and associates each story run with exactly one child. It does not specify a Facebook-style switcher or persistence across sessions. Parent Web target-client status remains open; no product requirement was inferred from the local preview.