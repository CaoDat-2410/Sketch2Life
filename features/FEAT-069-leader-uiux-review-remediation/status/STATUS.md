# Status

## Rev6 closeout and Rev38 review — 2026-11-14

- **State:** Rev6 Parent home adjustment is implemented and build-verified. Rev38 comparison is complete as a source/design review. Overall alignment to the two leader folders is **partial, not 100%**; the exact findings are in `evidence/notes/REV38_FLOW_ALIGNMENT_20261114.md`.
- **Approved scope:** `plan/PLAN_REV6_PARENT_HOME.md`, SHA-256 `B5AF1EB11C4DB22B2F4EC60F78786D5E62A3025E5638531BCC00BE0C24BA8CB1`.
- **Parent home:** Removed the duplicate selected-child summary. Child choice remains in story setup and Family Profile. Local Parent preview check confirmed the create-story CTA and navigation remain.
- **Build:** `npm run build` from `UI_Project` passed all five workspaces; `git diff --check` passed. No tests were added/run and no APK runtime check was performed in this step.
- **Product boundary:** Rev38 is generated proposal material; FEAT-063 SRS v2.5-draft remains the current unsigned working SRS. The review found the Parent idea/subject ordering conflict plus incomplete import, video job/playback, Manager publication checklist and Admin operational states. All role UIs remain offline previews; no API/auth behavior is claimed.

- **Feature:** FEAT-069 — Leader review UI/UX remediation.
- **State:** Rev5 implementation is complete and published under the approved preview-completion plan; final APK install/runtime on the supplied emulator is still unverified because Android Package Manager did not return from `adb install`.
- **Active plan:** `plan/PLAN_REV5_PREVIEW_COMPLETION.md`, SHA-256 `F49F00D71E5E0D84B2EA695A1BB63010DA2E82E8A8FAC356542BDA145279262A`.
- **Branch:** `FE_UI_Project_Ver2`.
- **Current scope:** APIs and source are business-flow references only. Parent, Teacher, School Manager, Platform Admin and shared web preview do not invoke `backendApi`, auth, `fetch`, or a backend request; data/actions remain local preview fixtures.
- **Parent UI:** Settings remains available only from Family Profile. Added a fixture mismatch review with two follow-up directions, an editable sample transcript flow, topic/difficulty-based three-step drawing guide, and gender display/edit on child selection and Family Profile. Gender is local preview state because the canonical unsigned FEAT-063 SRS and reviewed contracts do not define it.
- **Teacher UI:** Dashboard totals and lists derive from local lesson-summary and assignment-shaped fixtures informed by the source contracts; no analytics endpoint or live API is claimed. Existing navigable class → lesson → session → slide/Sketch → interaction → separate sample preview remains in place.
- **Other web roles:** School Manager and Platform Admin remain role-specific web workspaces with clearly labeled preview data and no server-action claims.
- **Verification:** `npm run build` passed all five UI workspaces. Parent Android typecheck passed. Debug APK packaging passed with the local Android SDK. Parent (including mismatch modal and gender/transcript flows) and Teacher dashboard were visually reviewed in the local preview; no automated tests were run.
- **Preview:** Parent `http://127.0.0.1:5171/`; Teacher `http://127.0.0.1:5172/`; School Manager `http://127.0.0.1:5173/`; Platform Admin `http://127.0.0.1:5174/`; shared web portal `http://127.0.0.1:5175/`.
- **APK:** `UI_Project/parent-android/apps/mobile/android/app/build/outputs/apk/debug/app-debug.apk` (built 2026-11-14). Emulator had booted, but installation produced no response and was interrupted; no app launch or runtime behavior is claimed. No emulator wipe/reset was performed.
- **Historical records:** Rev3 API crosswalk/commit remain historical. Rev4 removed UI-level API wiring; Rev5 remains UI-only. See `evidence/notes/EXECUTION.md` and `evidence/notes/OPEN_QUESTIONS.md`.
- **Publication:** Rev5 implementation commit `0a2cdd75` (`feat(ui): complete leader preview flows`) was pushed as a normal fast-forward from `35f2f055` to `origin/FE_UI_Project_Ver2` on 2026-11-14 (Asia/Saigon). Security validation passed before commit and immediately before push. See `evidence/notes/PUBLICATION.md`.
