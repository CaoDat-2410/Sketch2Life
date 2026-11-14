# FEAT-069 Plan Rev8 — full UI flow audit and visual polish

- **Status:** APPROVED by the owner's direct instruction in this conversation; record the plan hash in both approval registers before implementation.
- **Date:** 2026-11-14 (Asia/Saigon).
- **Branch:** `FE_UI_Project_Ver2`; work in the current checkout.
- **Scope:** Audit the primary `UI_Project/` Parent, Teacher, School Manager, Platform Admin, and shared web portal mockups against the leader's Rev38 screen/component folders, the supplied leader review action items, current FEAT-063 SRS v2.5-draft, and mounted/source API evidence. Correct demonstrated UI/UX gaps and harmonize color/contrast. Use fictional local fixtures and local state only.

## Authority and boundaries

- Read `docs/context/SRS_AUTHORITY.md` and `docs/context/SOURCE_REGISTER.md`. FEAT-063 v2.5-draft remains the canonical working SRS and is unsigned. Rev38 mockups are generated proposals based on older SRS/API material; they guide visual design but do not override the current SRS.
- Keep Parent's outdoor-activity selection after the story/video is ready as specified by SRS §5.1. The leader review asks for activity selection before video/script in one passage; keep this disagreement open and do not represent the ordering as leader-approved or product-final.
- Correct the Parent sequence to prepare/optional guide → capture → idea or editable voice transcript → subject confirmation/edit → minimum-context confirmation → story/script review → illustrative job states → video preview → activity selection. Do not add a separate context-choice screen. Mocked analysis/transcription must be labeled as preview data.
- Keep lesson-vs-drawing priority and mismatch choice after a captured image and the mock analysis result. Do not preselect the lesson direction at lesson-picker time. Preserve the two-choice mismatch dialog and make the selected choice explicit before script review.
- Remove the end-user “use sample drawing” action. Keep real camera/gallery selection; do not add a sample image or perform a real upload as a substitute.
- Preserve prior owner decisions: Parent Settings only appears under Family Profile; no selected-child summary card on Parent Home; gender remains a local-only preview field in child selection/profile; four other roles remain web workspaces.
- Keep all experiences as local mockups. Do not call `backendApi`, `fetch`, auth, external links, AI/ASR, payment, mail, storage, or network; do not change backend/API/schema/SRS/auth/data, legacy top-level `apps/`, Child Expo, or Rev38 source boards. Keep any values that lack a mounted contract clearly labeled as fictional preview data.
- No generated bitmap assets are needed. Use code-native styling and the Rev38 blue-primary, subdued-yellow-accent, mint-support direction with readable contrast and calm surfaces.
- Store evidence under this feature's `evidence/`; update decisions, open questions, execution, status, source register and publication notes after meaningful review/implementation stages.

## Deliverables

1. A traceable audit mapping Rev38 P01–P12, T01–T07, M01–M02, A01–A02 and UI01–UI09 to reachable routes/steps, canonical SRS behavior, local fixture-only behavior, and evidenced API support or gap.
2. Correct Parent step order and guard behavior; move the minimum-context confirmation after subject review, defer story direction choice until mock analysis, retain the mismatch modal, and remove the sample-drawing action. Keep transcript text editable and its preview status concise.
3. Rebalance the Parent and four web workspaces to a calm Rev38-inspired palette, with dark readable text, clear focus states, softer yellow/mint surfaces, and danger/error red reserved for those states. Do not redesign workflows that already meet the approved flow.
4. Keep Teacher session/detail, Manager publication gates, Admin status-driven moderation, and shared portal/recovery role routes reachable with fixture labels. Do not claim unimplemented API behavior or analytics.
5. Update FEAT-069 audit/evidence/status records with full scope, current API boundaries, remaining decisions, verification results, and known runtime limits.

## Acceptance criteria

- **AC1 — coverage:** every Rev38 screen/component ID is mapped to a reachable UI state or a documented, intentional local-only/unresolved state. The route list is checked against current source rather than inferred from folder names.
- **AC2 — Parent flow:** Parent transitions follow the current SRS sequence listed above; context is confirmed after subject; lesson/drawing direction is not selected before the captured-image mock analysis; mismatch offers both intended choices; no sample-image action is visible.
- **AC3 — role flows:** Teacher, Manager and Admin remain role-specific web previews with all approved primary/detail flows reachable; any unsupported metrics/action are visibly marked as preview data. Parent remains the mobile workspace.
- **AC4 — UX/design:** the palette is calmer and text/control contrast is visibly clearer across all five workspaces; buttons, modal actions, disabled/error states and keyboard focus remain distinguishable.
- **AC5 — integration boundary:** no API/auth/network/storage/payment/AI/ASR connection or data persistence is added; fixture shapes and provenance are documented so later API work can replace values without moving screen layout.
- **AC6 — review:** all five workspace builds pass; Parent Android typecheck and debug APK packaging pass; manual browser visual review covers Parent flow plus representative Teacher, Manager, Admin and portal pages. Emulator runtime is reported only if an Android device is actually attached and launched.
- **AC7 — unresolved requirements:** the outdoor-activity timing conflict, gender-contract gap and uncovered backend/API capabilities are called out explicitly. Do not claim 100% leader acceptance or production/API readiness without owner/leader sign-off.
- **AC8 — repository controls:** `git diff --check` and `python tools/validate_repository_security.py` pass; run the repository security validator immediately before each commit and push. No automated tests are added or run.

## Approval basis and explicit exclusions

The owner directly requested an end-to-end recheck against the two leader-provided Rev38 folders, the leader review/action items, current project source and available APIs; asked that any gaps be added; authorized fictional data for the UI mockups; asked for improved UX and a less bright palette; and said the deliverable must not need a UI redesign when real API values are connected later. This authorizes the bounded UI-only scope above.

Excluded: API/backend/auth/schema/SRS/data-model changes; real data or persistence; external calls, AI/ASR, email, payment, uploads or production actions; legacy `apps/` and Child Expo; generated raster assets; automated tests; force push/history rewrite; and claims of formal leader approval or complete API readiness.
