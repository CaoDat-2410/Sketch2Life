# FEAT-073 Plan revision 1 — Child profile gender and matching avatar

- Revision: 1
- Status: APPROVED after recording the owner's direct request in the worktree approval ledger.
- Prepared: 2026-11-10
- Product authority: FEAT-063 SRS v2.7-draft, updated 2026-11-07, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off.
- Active implementation target: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.

## User request

“phần tạo hồ sơ thiếu giới tính nữa ví dụ như là giới tính nam thì avatar là đứa bé trai nếu là con gái thì là avatar đứa bé gái á”

## Goal

Add a clear gender choice to the child-profile create flow and make the avatar consistently follow that choice: Nam shows the boy illustration; Nữ shows the girl illustration. Keep the control and preview within the existing Parent visual system.

## SRS mapping and authority boundary

- Canonical product requirements are FEAT-063 SRS v2.7-draft §§1–31, routed by F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md.
- FR-PL-25 / BR-57 constrain profile age to 36–120 months; FR-PL-18 requires the selected child profile context to remain attached to that child's story/video.
- A search of the canonical SRS found no gender field or gender-specific avatar requirement. This implementation is authorized by the owner's direct request, is limited to the existing local FE demo profile model, and does not modify or claim a new SRS requirement.
- Do not send gender into story/AI context or add an API, persistence, analytics, or backend contract. Record the product/schema question as open for later formalization.
- Existing profile fixtures will get explicit demo-only gender values matching their current illustrative avatars, so existing mock visuals remain stable. These fixture choices are not inferred from profile names or real-child data.

## Current implementation evidence

- The Add Child sheet is owned by MobileLayout and calls ParentContext.addProfile.
- ChildProfileItem has no gender property.
- ChildAvatarSvg currently decides boy/girl from an array index, so the avatar can change when profile ordering changes.
- The P13 profile list, P01 child switcher, and P10 profile detail render this avatar. P10 detail is the existing edit flow for the profile.

## Scope

- Add a typed gender field to the local ChildProfileItem and explicit demo fixture values.
- Add an accessible two-choice Nam/Nữ selector with both avatar previews to the Add Child sheet.
- Allow the existing profile detail form to edit the choice and preview the matching avatar before save.
- Make P01, P13/P10 profile rows, and profile detail render from the profile's selected gender instead of list index.
- Update ParentContext add/update operations to carry the local field in session state.
- Reuse inline SVG avatars and app tokens; add no image asset or dependency.
- Add FEAT-073 context, decisions, approval, status, and evidence records.

## Explicit boundaries

- Keep the gender value local to the synthetic Parent UI profile object. No API, backend, SRS, database, storage, AI personalization, consent, or analytics changes.
- Preserve existing age validation, profile selection, archive/delete, consent, and navigation behavior.
- No account or auth changes; preserve the existing in-flight FEAT-036/067–072 work.
- No automated tests/builds, commit, push, deployment, or publication.

## Implementation steps

1. Add a ChildGender type and a required local gender field to ChildProfileItem; set deterministic demo values that preserve the current sample avatars.
2. Replace index-derived avatar selection with the explicit gender value at every Parent profile avatar call site.
3. Add a reusable accessible radio selector with boy/girl avatar previews; require a selection when creating a profile.
4. Add gender editing and live avatar preview to the existing profile detail form.
5. Manually review create, save, profile switcher/list, edit, and responsive behavior in the active port-5171 preview. Record screenshots/findings under FEAT-073 evidence.

## Acceptance criteria

1. Add Child includes a labeled, keyboard-operable Nam/Nữ choice and shows the matching boy/girl avatar in each option.
2. The create action remains unavailable until name, valid age, and gender are selected; saving creates a profile with its chosen gender in session state.
3. The saved avatar remains the same in the P01 child switcher, P13 profile selector, and profile detail regardless of list ordering.
4. Editing gender updates the preview immediately and the saved avatar after save.
5. Existing demo profile avatars keep their current illustration; fixture gender is explicit rather than inferred from names.
6. Selection has a visible focus and selected state, touch-sized cards, and accessible labels at phone and tablet widths.
7. Age validation, profile selection, consent, archive/delete, and routes continue to work.
8. Gender is used only to choose the local avatar; no API, persistence, or AI-context behavior is added.

## Verification boundary

Use the active local Parent UI preview for manual interaction and visual review. Do not run automated tests or builds under this plan. Store evidence only in this feature's evidence directory.
