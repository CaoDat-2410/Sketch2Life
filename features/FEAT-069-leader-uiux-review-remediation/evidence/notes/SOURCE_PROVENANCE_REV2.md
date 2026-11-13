# FEAT-069 Rev2 source provenance

Date: 2026-11-14
Target branch: `FE_UI_Project_Ver2` at `2518dc074eba9d970306f82ceff8998d37f13535` before Rev2 implementation.

## UI target

The project owner confirmed that `UI_Project/` is the primary UI/UX to revise. The top-level `apps/` tree is legacy UI and is excluded from this handoff's source and run targets. `UI_Project/parent-android/apps/mobile` is the Parent APK host; its `ParentWebPreview` loads the bundled `UI_Project/parent-ui` page. `UI_Project/parent-android/apps/ui-mobile` is a separate workspace and is not the target for this leader-review task. Teacher, School Manager, and Platform Admin use the role workspaces under `UI_Project/`.

## Requirement authority

`docs/context/SRS_AUTHORITY.md` identifies the FEAT-063 SRS v2.5-draft as the canonical working requirements source. It remains an unsigned draft. Leader review material controls this UI review task only where the owner explicitly approved a preview divergence; it does not amend the SRS or API contracts.

## API source comparison

The delivery-branch route mount at `backend/src/sketch2life/interfaces/http/router_composition.py` mounts the BE1 runtime, demo routes, and Lesson Library routes. It does not mount Parent profile, Parent AI, or Parent story-run router groups. A read-only comparison with the newer permitted backend source `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e` found those additional router groups in `mount_all_routers`; their presence in that other source branch does not make them available to teammates cloning `FE_UI_Project_Ver2`.

For this handoff:

- UI actions may use the current local preview state and must identify fixture/preview data.
- A route is represented as connected only when it is mounted in the delivery branch and its required identity/context is available.
- Parent profile/story/AI operations remain preview-only on this branch. No live AI/provider call or API write is made.
- Lesson Library, Teacher lesson, School Manager grant-review, Platform Admin moderation, and BE1 class/roster/consent screens follow the contracts catalogued in `features/FEAT-068-project-uiux-coverage/evidence/notes/API_UI_CROSSWALK.md`; existing role screens remain previews without a supported authenticated identity bridge.

## Source branches read

- `origin/feature/feat063-m2-parent-teacher-foundation` at `5c07c94e`: backend router composition/API availability comparison only; no source files copied.
- `origin/feature/fe-ui-full-remediation` and `origin/feature/fe-mobile-remediation`: read-only branch metadata was inspected while selecting a source. Their top-level `apps/` UI trees were excluded after the project owner identified them as legacy. No code was copied from them.

## Limits

This is source-registration evidence, not a runtime API health check. No backend was started, no request was sent, and no auth/session or tenant context was fabricated.
