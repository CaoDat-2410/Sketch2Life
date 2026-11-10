# FEAT-073 — Child profile gender and matching avatar

- Status: COMPLETE; Plan Rev1 is approved and hash-recorded in the worktree root approval ledger.
- Active worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Runtime target: Parent UI preview at http://127.0.0.1:5171.
- Product authority: FEAT-063 SRS v2.7-draft (2026-11-07), SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; pending formal owner sign-off.
- SRS mapping: FR-PL-25 / BR-57 (36–120 month profile age range), FR-PL-18 (selected child profile context).
- Open requirement: the canonical SRS does not specify a child gender field or gender-specific avatar behavior. This feature follows the owner's direct request and is limited to local Parent FE demo state; it does not change SRS or API contracts.
- Authority discrepancy: this worktree has stale local v2.5 authority files. The user-provided project instructions and main checkout authority cite v2.7; v2.7 is used, and stale copies remain unchanged.

## Baseline

The Add Child sheet records name, age, and interests. ChildProfileItem has no gender. ChildAvatarSvg derives boy/girl from the current list index, so avatar choice is not stable when ordering changes.

## Implementation and review

- Added required `male` / `female` gender to local `ChildProfileItem` demo state. Seeded fixture values preserve the existing Minh/An avatar illustrations explicitly.
- Added a keyboard-operable Nam/Nữ radio choice with both avatar previews in the Add Child sheet. Save stays disabled until a name, selected gender, and valid age are present; the existing 36–120 month validation remains in place.
- Added a live gender choice and avatar preview to the profile detail form. P01 and P13/P10 profile views now use the profile's saved gender rather than profile order.
- Reused inline SVG artwork and local tokens. No image assets or dependencies were added.
- Interactive review in isolated Edge 157 against the active port-5171 Vite preview: create a male profile with Tab + Space, verify the boy avatar in settings and P01, edit to female, verify the live girl preview and saved avatar in settings/P01. Confirmed age 121 disables Save and the valid 120-month boundary enables it. Checked 390×844 phone and 768×1024 tablet viewports; neither had horizontal overflow. No browser runtime exceptions were observed.
- Source review confirms profile data remains React session state; the gender field is not written to local storage or sent through an API/AI-context path. The only existing local-storage use in ParentContext is the display theme.
- Automated tests and builds were not run, per the approved plan. No commit, push, or deployment was performed.

## Remaining product question

The canonical SRS does not define a child gender field or avatar behavior. This FE demo follows the owner's direct request only. Formal product/schema/API decisions remain open for a future approved SRS/contract update.
