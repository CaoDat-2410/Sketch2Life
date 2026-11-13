# Feature decisions

## D-069-01 — Canonical product requirements

Use FEAT-063 SRS v2.5-draft as the working target. Leader transcript items that conflict with it remain open owner questions; do not silently change activity order, child-profile data, or AI flow contracts.

## D-069-02 — Parent transcript and AI guide truthfulness

Keep adult transcript editing/review while removing redundant instruction copy. Do not imply ASR or line-sketch AI is connected. A code-native static guide may be topic-aware but must not use child profile/media.

## D-069-03 — Context confirmation

Use a compact confirmation dialog in place of a separate context-selection page. The adult still reviews and confirms the allowed context snapshot before story generation, as required by FR-P-06.

## D-069-04 — API data boundary

Teacher role screens remain preview-only until an authenticated principal and organization context can be resolved through a supported bridge and mounted endpoint. Do not seed tenant IDs or claim fixture counts came from backend.

## D-069-05 — Rev2 leader review prototype scope

The user explicitly approved completing all remaining leader-review UI items under Plan Rev2. For reviewability, the Parent pre-video activity sequence and local gender control may be shown in preview UI even though they differ from or are absent from the canonical SRS/API. Keep FEAT-063 SRS v2.5-draft unchanged, label simulated AI/data states honestly, preserve the required adult context confirmation, and record these product decisions as unresolved pending formal owner/SRS sign-off.

## D-069-06 — UI source boundary and current-branch API availability

The user confirmed that `UI_Project/` is the project's primary UI/UX and that the top-level `apps/` tree is legacy UI that must not be used for this handoff. Keep the approved Parent Android/WebView and three-role web workspaces under `UI_Project/` as the implementation and run targets. Do not copy, launch, or register top-level `apps/` UI workspaces as part of this feature. A read-only comparison against the permitted newer backend source `origin/feature/feat063-m2-parent-teacher-foundation` at `5c07c94e` showed Parent profile/story routers there that are absent from the delivery branch `FE_UI_Project_Ver2` at `2518dc07`; only routes mounted in the delivery branch may be described as available to a teammate cloning this branch. Keep other Parent operations preview-only until their routes are present and authenticated in the delivery branch.

## D-069-07 — Parent APK presentation target

The Parent UI shown in the browser is the bundle rendered inside `UI_Project/parent-android/apps/mobile` by `ParentWebPreview`. Keep `UI_Project/parent-ui` as the canonical Parent UI implementation and ensure the Android debug APK packages that same bundle. The separate `UI_Project/parent-android/apps/ui-mobile` workspace is not the target of this leader-review task.

## D-069-08 — Rev3 conditional API reads and truth states

The approved Rev3 scope connects only current, mounted read contracts that can be safely scoped by an injected Firebase token bridge and organization ID: Teacher Lesson Library lessons, Teacher BE1 assignments, and School Manager BE1 classes. Teacher/Manager dashboard measures are derived from those returned rows, not from a dedicated analytics endpoint. Without auth/config, retain labeled preview data; with auth/config but missing organization context or failed reads, show unavailable/error states and do not replace API results with fixtures. Keep Teacher/Manager writes, Parent operations, Platform Admin queue, and all routes present only on the read-only comparison branch preview-only. Do not claim a full live workflow or connected login until the delivery branch has a supported identity bridge/handler and missing contracts.
