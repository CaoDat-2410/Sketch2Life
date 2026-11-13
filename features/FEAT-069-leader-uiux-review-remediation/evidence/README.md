# FEAT-069 evidence index

Evidence for the leader-review remediation, captured 2026-11-14 (Asia/Saigon). The approved scope reconciles leader feedback against FEAT-063 SRS v2.5-draft and the mounted API surface.

| Evidence | AC | What it establishes | Limitations |
|---|---|---|---|
| `notes/EXECUTION.md` | AC2, AC4–AC10 | Build/typecheck/APK build results, browser visual checks, emulator install blocker, and the exact evidence set | APK was built but the updated build could not be installed on the supplied emulator because Android Package Manager was failing. |
| `notes/OPEN_QUESTIONS.md` | AC3, AC8 | SRS/API conflicts and unmounted integrations requiring product/owner decisions | Questions are explicitly unresolved; no behavior is inferred from the leader transcript. |
| `screenshots/parent-home.png` | AC6, AC9 | Parent home hierarchy, create CTA, global settings and center create action | Browser-rendered phone preview; not a screenshot from the rebuilt APK. |
| `screenshots/parent-lesson-picker.png`, `parent-lesson-picker-groups.png` | AC1, AC9 | Lesson selection stays in story setup; system-public and school/teacher-shared groups are visibly distinct; details are available in place | Lesson cards use local preview data, not an API response. |
| `screenshots/parent-sketch-guide.png` | AC2, AC9 | Optional guide is step-based, skippable and labeled static/not AI-generated | The guide is an illustration-only preview. |
| `screenshots/teacher-session.png`, `teacher-session-interaction.png` | AC7–AC9 | Teacher flow presents class/lesson/activity, optional static Show Slide/Sketch, interaction, and a separate sample-story entry | Session, deck and dashboard remain browser-local preview state. |
| `screenshots/school-manager-dashboard.png`, `platform-admin-dashboard.png` | AC9 | Both other web role entry points still render and disclose preview/fixture data | Dashboard-only visual review; no live API behavior is claimed. |

All captures are stored in this feature folder. No child media or real profile data was used.
