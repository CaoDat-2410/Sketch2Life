# FEAT-066 goal v3 Phase D - Android Parent wiring: evidence note (2026-11-22)

Status: checked and committed; one commit on `feature/v3-phase-d-mobile`; not pushed. Codex (gpt-6.1-terra, high) did the first pass (summary outside the repository: `tmp/codex-parallel/mobile-phase-d/SUMMARY.md`, audit left incomplete); the audit was completed by an independent Sonnet 5.5 (high) reviewer. Backend read (read only): Phase D squash `8c1cf931` on `feature/backend-srs-api-and-fe-integration`; per-task commits `5d1af59b..c47cd6d8` on `feature/backend-srs-api-v3` (T-4b1 `82c59bdb`, T-4b2 `8d0fd2ed`, T-4b3a `29949961`, T-4b3b `79f85c86`, T-5a `c47cd6d8`).

## 1. Result

The backend range changes nothing the Parent app calls or reads. The Parent app keeps working unchanged for: `POST /v1/story-runs` (role-dispatched, Parent handler untouched), list, active run, detail with ETag, context/subject/script confirmation, cancel and delete, `/assets`, `/idea`, `/transcript`, `/transcript-confirmation`, `/story-rewrites`, `/video-generations`, `/video-unsuitable`, `/complete`, `/playback-token`, `/playback` (a Parent token carries no projection claims), `/v1/upload-sessions` (`RUN_ARTWORK`, `RUN_AUDIO` gain a Teacher role only), `GET /v1/jobs/{id}`, `/api/parent/v1/ai/*`, notifications and the lesson library (not in the diff). The sweepers and the input reaper add a Teacher branch only; no new run, generation or job state and no new code reaches a Parent. New codes (`TEACHER_ACTIVE_RUN_CONFLICT`, `SAMPLE_VIDEO_ALREADY_EXISTS`, `LESSON_PLAN_NOT_APPROVED`, `MULTI_CHILD_NOT_SUPPORTED`, `TEACHER_ASSIGNMENT_REQUIRED`) are reachable only by a Teacher account or a Teacher-shaped body; the app already degrades unknown codes to safe copy. Child-selection and projection routes are Teacher only; no Parent flow calls them.

## 2. What changed (all under `apps/ui-mobile` and this feature folder)

- `ParentApi.createStoryRunV1` serialises only the Parent create fields (and the three-field lesson pin) explicitly, so a Teacher-shaped key can never reach the Teacher branch of the dispatcher. `lesson_version` omitted stays omitted, `null` stays `null`.
- Tests: create body pin (Teacher keys dropped, omitted and null pin cases), unknown run fields and unknown run state degrade safely (non-vacuous after review), playback error cases (invalid grant refreshed once, 404/416/503 safe).
- Plan file `plan/PHASE_D_MOBILE_WIRING_PLAN_20261122.md` (written by Codex on the owner's launch instruction; BOM removed).

## 3. Checks (final state)

- `apps/ui-mobile`: `npm test` 18 files, 223 tests passed, `UI_COPY_AND_RECOVERY_VALID`; `npm run typecheck` 0 errors.
- Worktree root: `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` valid; `git diff --check` clean.
- Not checked: backend golden tests (read from the evidence notes: 2,578 and 2,188 Parent answers unchanged), a device, live playback.

## 4. Review

Sonnet 5.5 (high), one round: ACCEPT WITH NOTES, no P1/P2; P3 fixed (vacuous assertion, missing null/omitted cases, BOM). Not fixed (P3): the serialiser could use a small helper; the 503 playback test body code is not the backend's; the playback invalid-grant test does not assert which token was used.

## 5. Open items for the coordinator and owner

1. The owner approval of this mobile task is appended to `approvals/TASK_APPROVAL.md` in the same commit (AGENTS.md rule 4); the plan file records the owner launch instruction.
2. SRS authority: the file used by goal v3 (`443A3CA3`) differs from the `docs/context/SRS_AUTHORITY.md` / `SOURCE_REGISTER.md` (`B9B1F42D...`) carried by this branch. Those two files are already updated on `origin/dev` and on the integration branch (`SOURCE_REGISTER.md` records `443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021` as canonical); this branch was cut from an older dev and the difference resolves when it meets dev. They were not hand-edited here.
3. No new Vietnamese string was added in Phase D.
