# FEAT-066 Rev28 — consolidated web structure and SRS UI review

Date: 2026-11-16 (Asia/Bangkok)
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`

## SRS baseline and source note

This task follows the SRS file the owner explicitly selected in chat: `F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev68, SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`. It remains unsigned.

The repository source register at `F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md` currently points to FEAT-063 v2.7-draft Rev60, SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`, also unsigned. This task does not update that authority record. The source-version mismatch remains open for the owner to reconcile; this evidence does not claim formal SRS sign-off.

## SRS-to-route and API matrix

| Role/surface | SRS target used for review | Active web/API state | UI decision |
| --- | --- | --- | --- |
| Shared entry and role login | Rev68 §§3, 9.2–9.3, 21.5 | Shared role chooser; existing sign-in/role-resolution adapter retained. Local preview is loopback-only and visibly non-persistent. | Keep roles separate and preserve authenticated role checks. Preview opens layout only; it does not claim backend access or save changes. |
| Teacher classes and roster | Rev68 §§5.2, 21.5, 31.3, FR-PL-07/08/20 | Existing assignment/class/profile/consent reads are retained and scope-filtered. | Display assigned scope only; do not ask Teacher to choose a child for the sample flow. No child fixtures are used. |
| Teacher lesson authoring and document import | Rev68 §§5.2, 21.5, 31.2/31.4, FR-PL-09–13 | Existing lesson CRUD/revision and source-document upload/extraction/review contracts are retained. | Show only API-backed lesson content and source-document states. Do not imply raw document text or embedded media is sent to AI. |
| Teacher occurrence, Sketch Deck and one-child sample run | Rev68 §§5.2, 21.5, 31.5, FR-PL-15–20 | No complete occurrence, server-selected eligible child, sample-run, quota, job/reconciliation, transcript/context review, playback, projection, or lifecycle contract is available in this FE adapter. | Render clear unavailable states and dependencies. No batch processing, manual child selection, fabricated progress, or successful run state. |
| Teacher lesson presentation | Rev68 §31.17 | Lesson API exists; slide/media draft, upload/provenance/review, and immutable published-revision lifecycle APIs are absent. | Show the target workflow and exact missing contracts as unavailable. Do not generate a fake saved deck, image, or revision. |
| School Manager BE1 | Rev68 §§21.5, 31.3 and related school-management flows | Firebase identity plus current organization assignment gate; BE1 class list/create and existing scoped lesson-public review are retained. | Keep BE1 authenticated routes separate from local preview. Capacity transitions, teacher assignment lifecycle, billing/payment, quota and inbox remain unavailable. School Manager has no default story/media access. |
| School Manager layout preview | Rev68 §§9.2–9.3 and 21.5 | Local M01/M02 preview only; no API calls, writes or review decisions. | Keep the non-persistent preview banner visible; preview M01 is not represented as a valid approval action. |
| Platform Admin operations/content | Rev68 §§21.5, 31.3, FR-PL-01/05 | Local `GET /health` exists but is not called by preview. No aggregate queue/job, billing reconciliation or lifecycle API is wired. Exact immutable-version moderation and capability discovery are absent. | Operations stay metadata-only. Content Admin remains a permission, not a role; do not expose child story/media by default or treat the route as granting a capability. |

The matrix describes the current web source and contracts inspected for this task; it does not assert that any unavailable target flow is implemented in the backend.

## Structure and implementation

- One active web app lives under `apps/web`: one Vite entry, one `BrowserRouter`, shared UI/session modules, and role-owned modules for Teacher, School Manager, and Platform Admin.
- Role applications are lazy-loaded to keep role-specific bundles separate. Root web scripts and CI point to `apps/web`.
- Superseded standalone web roots were removed after source/import/asset review. Existing user-requested app-folder removals are captured in the worktree baseline; `apps/ui-mobile` and `apps/api` remain outside the web app.
- The shared shell provides role navigation, responsive drawer, visible preview/API state, skip link, focus styling and logout while preserving the existing auth/API boundaries.
- Manager preview and BE1-backed school-admin remain separate routes and session behavior.

## Browser and responsive review

Nine loopback captures are stored under `evidence/screenshots/web-rebuild-rev28/`:

| Capture | Route | Viewport |
| --- | --- | --- |
| `entry-1440.png` | `/login` | 1440×900 |
| `teacher-dashboard-1440.png` | `/teacher/t01-lesson-workspace` | 1440×900 |
| `teacher-dashboard-768.png` | `/teacher/t01-lesson-workspace` | 768×1024 |
| `teacher-dashboard-390.png` | `/teacher/t01-lesson-workspace` | 390×844 |
| `teacher-mobile-menu-open-390.png` | `/teacher/t01-lesson-workspace`, drawer open | 390×844 |
| `teacher-presentation-1440.png` | `/teacher/t02-presentation` | 1440×900 |
| `school-manager-preview-1440.png` | `/school/preview/m02-organization-management` | 1440×900 |
| `school-manager-login-390.png` | `/school/login` | 390×844 |
| `platform-operations-1440.png` | `/platform/a02-platform-operations` | 1440×900 |

All nine images were visually inspected. The 390px dashboard capture was recaptured after the first file showed the drawer mid-transition; the final image shows the drawer closed. A fresh local browser measurement recorded `innerWidth=390`, `documentElement.scrollWidth=390`, main width 390px, and `aria-expanded=false`. The drawer keyboard pass opens the menu, focuses the first link, then Escape closes it and restores focus to the trigger. These captures use local preview state only; no production service, child data or credentials were used.

## Build and known limits

- `npm ci` completed for `apps/web`; `npm run build` passed after the explicit-role-route fix. Vite produced separate role chunks; the main JS chunk is approximately 281 KB (90 KB gzip).
- Installation reported four high-severity npm audit findings and skipped the install scripts for `@firebase/util` and `protobufjs`. No dependency audit fix or version change was made.
- No application tests were run, as instructed. No authenticated production API, live Firebase session, deployment host, or production data was exercised.
- The host's deep-link fallback remains unverified. Role pages that lack backend contracts remain intentionally unavailable.
- Required repository security/harness/architecture validator results and final `git diff --check` are recorded in the closeout evidence after they run.

## Final repository validation — 2026-11-16

- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`; 7,357 publishable files scanned, environment/credential files excluded, no absolute machine paths. The first scan found local absolute paths in the old Rev23 provenance note; those paths were normalized to local/external descriptions and the final scan passed.
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`; dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary and Firebase data-product constraints passed.
- `git diff --check`: exit 0. Git printed only line-ending normalization warnings for existing CRLF markdown files.
- `python tools/validate_harness.py`: `HARNESS_INVALID` because `apps/mobile/package.json` is absent (the owner had explicitly requested removal from this branch) and unrelated FEAT-070 evidence directories are missing.
- `python tools/validate_skeleton.py`: cannot run because it reads the intentionally removed `apps/mobile/package.json`.
- `npm ci` and `npm run build` passed earlier in this closeout. No app test suite was run.
- The mobile app and unrelated FEAT-070 scaffold were not recreated to satisfy those validators; doing so would reverse the requested folder cleanup or expand this web task.
