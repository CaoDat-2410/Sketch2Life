# FEAT-069 Plan Rev7 — complete project UI mockup flows

- **Status:** APPROVED by the owner's direct request in this conversation; record this exact plan hash in both approval registers before implementation.
- **Date:** 2026-11-14 (Asia/Saigon).
- **Branch:** `FE_UI_Project_Ver2`; keep the current checkout and its allowed source history.
- **Scope:** Complete the UI-only mockup flows across the primary `UI_Project/` Parent mobile workspace, Teacher web workspace, School Manager web workspace, Platform Admin web workspace, and shared web portal, using the owner-provided Rev38 screens/components as the visual and flow reference. Use local fictional fixture data and local state transitions only. Include the Parent profile-action spacing defect in the supplied screenshot.

## Authority and boundaries

- Current product reference remains FEAT-063 SRS v2.5-draft under `docs/context/SRS_AUTHORITY.md`; it remains unsigned. The owner directly asked this UI mockup to follow the leader-provided Rev38 flow. Where Rev38 and the SRS differ (notably Parent idea/subject ordering), implement the requested Rev38 order in the visual prototype only, keep the SRS/API unchanged, and preserve the conflict as an explicit open product question. Do not represent this as product/API sign-off.
- Keep `UI_Project/` as the only UI implementation target. Do not modify the legacy top-level `apps/` tree, Child Expo, backend, API, schemas, auth, persistence, provider configuration, SRS, or migrations.
- Do not issue API/auth/network requests or add a client integration. All screen records and status transitions use typed fictional fixtures/local state. Keep presentation components separate from fixture repositories/view models so a future approved data adapter can replace fixture inputs without redesigning the screens.
- The user previously requested Parent Settings only from Family Profile, no selected-child summary card on Parent home, and a gender display in child selection/profile. Preserve those requests; add the profile picker entry to Parent Library P01 rather than restoring a home card. Gender remains preview-only.
- Use existing approved/code-native assets and layout. Do not generate/copy bitmap artwork in this plan; do not modify Rev38 source boards. Keep one consistent fictional child/artwork through Parent capture/story/video previews and synthetic records in web roles.
- Rev38 tokens are owner-requested mockup guidance for this visual pass (blue primary, yellow accent, mint support, warm-white surfaces); applying them here is a UI proposal, not production-token approval.

## Deliverables

1. **Parent P01–P12:** Library with child switcher, sample quota and resume card; lesson detail; integrated optional drawing-guide/capture surface; capture then subject confirmation; idea/transcript and minimal context review; structured story review with a three-rewrite limit; four-stage background-job status with resume/failure/safety states; sample video playback/captions followed by activities; history/lesson feedback; child-profile list/edit/archive; local authentication/recovery mock; and quota/top-up mock. Preserve run ordering and confirmation gates within the Rev38 prototype. Do not invent a confidence percentage, video ETA, public video link or real payment outcome.
2. **Teacher T01–T07:** compact dashboard centered on next class/session and lesson/feedback summaries; four-section lesson authoring with structured activity cards; a three-step document upload → extracted-field review → confirmation flow; occurrence preparation with optional Sketch Deck; assigned class/child roster; one eligible sample-story run with adult script confirmation; and private sample-video preview with captions and explicit occurrence presentation confirmation.
3. **School Manager M01–M02:** version-specific publication queue/detail with content/version tabs, four unchecked checklist gates, disabled approve until all pass, and an enabled request-changes path; organization workspace for teachers/groups/classes/slots/quota using local fixture transitions.
4. **Platform Admin A01–A02:** searchable/filterable catalog moderation table and detail panel with actions determined by each row's effective status; operations overview for organizations/catalog/policy/quota/audit with fictional counts and local detail navigation.
5. **Shared UI01–UI09:** apply consistent foundations, dialogs, decision confirmations, feedback/toasts, loading/empty/error/safety states, teacher import review, job/quota states, lesson/profile grant states, and lesson-scoped feedback to the relevant flow pages. Reduce visible role navigation to the Rev38 six-section structure while keeping in-scope detail screens reachable through their parent sections.
6. **Parent profile spacing:** separate primary edit and destructive delete/archive actions with clear vertical space and responsive behavior; preserve confirmation and disabled states.
7. Update FEAT-069 decisions, questions, evidence, status, source register and publication records. Build all five workspaces, typecheck/package the Parent Android WebView bundle, manually inspect the primary Parent flow and representative Teacher/Manager/Admin routes, and run repository security validation before every commit/push. Do not add or run automated tests.

## Acceptance criteria

- **AC1:** Every Rev38 screen ID P01–P12, T01–T07, M01–M02 and A01–A02 has a reachable, visually coherent screen/step in the correct role workspace. Primary role navigation follows the six Rev38 sections; detail flows remain reachable.
- **AC2:** Parent can navigate a complete fictional path from child/lesson selection through optional drawing guidance, capture/subject review, idea/context, script confirmation, job status, sample playback, and only then lesson activity. Relevant secondary routes (history, feedback, profile/auth/quota) have their own complete local preview states.
- **AC3:** Teacher can walk through lesson creation/import/review, class/roster, occurrence/deck, sample story and presentation confirmation. Document fields are editable fixture values; no selected file is parsed or uploaded.
- **AC4:** Manager's approve control remains disabled until every required checklist item is checked; request-changes requires feedback. Admin moderation actions and resulting detail states match each row's effective status.
- **AC5:** UI screens consume typed fixture/view-model data and state-driven local handlers. No backend/API/auth/network calls, uploads, emails, payment redirects, AI/ASR, or persistent data writes are added. Replaceable fixtures carry no real user/child information.
- **AC6:** The Parent profile action buttons no longer touch/overlap at the supplied viewport and remain spaced at narrow mobile sizes; the Parent home still has no selected-profile summary card and child selection remains available in story setup and Library.
- **AC7:** Current SRS/Rev38 conflict, any intentionally local-only state, and the inability to promise compatibility with future unknown API response contracts are documented without changing the SRS.
- **AC8:** All five `UI_Project` workspace builds pass; Parent Android typecheck and debug APK packaging pass; manual browser/emulator review records exact routes and limits; repository security validator passes before commit/push.

## Explicit approval basis

The owner directly instructed: complete mockups for the entire project's UI/UX, make them follow the leader-provided flow, use sample data so a later API connection changes data rather than screen design, and not integrate APIs now. The owner also supplied the Parent profile screenshot showing overlapping actions. This is approval for the bounded UI-only scope above. It does not approve production SRS changes, API/auth integration, actual payments, data persistence, or changes outside `UI_Project/`.
