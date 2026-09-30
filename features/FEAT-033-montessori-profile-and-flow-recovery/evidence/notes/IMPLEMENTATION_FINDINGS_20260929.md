# FEAT-033 implementation findings — 2026-09-29

This note contains synthetic/test-fixture evidence only. No real child profile, drawing, audio,
free text, credentials, or provider response is included.

## Reproduced request validation failure

- The earlier production request body was not captured, so the exact historical failing value cannot
  be proven after the fact.
- A regression test replaying the current mobile V2 request through candidate discovery and
  finalization did reproduce a producer/schema mismatch: catalog options included reviewed
  `MAT_…` material IDs while `ChildLearningProfileContextV1/V2` accepted only `GMAT-…` IDs.
- The sanitized validation path was `child_profile.available_material_option_ids`, code
  `value_error`; no submitted value is logged or returned.
- Validation now accepts only the existing `MAT_[A-Z0-9_]+` and `GMAT-[A-Z0-9-]+` namespaces. The
  versioned V2 end-to-end contract test verifies the current mobile payload succeeds; it also
  verifies unknown profile fields return the safe typed failure instead of the generic unreadable
  response.
- The V1 contract remains available. The new V2 error provenance identifies its source contract.

## Profile, candidate, and supervision flow

- Mobile profile fields are session-volatile. Free text is capped at 240 characters per field and
  sent only on explicit AI classification; the adult reviews/selects tags before use. No raw text
  enters application logs or the final activity request.
- V2 profile schema has no progress/history or profile-level supervision-availability field.
- Candidate discovery returns at most three topic/age matches with authored readiness metadata.
  It filters incomplete (`UNSPECIFIED`) readiness records before selecting the bounded shortlist,
  preventing all shortlist slots from being consumed by activities that cannot be finalized safely.
- Finalization recomputes the shortlist on the server, rejects any different client-supplied ID
  set, and considers only activities for which the adult confirmed the exact displayed supervision
  requirement. Readiness, material groups, prerequisites, supervision, and safety remain hard
  eligibility gates; interest/dislike tags only adjust ranking among surviving related activities.
- Vietnamese labels now map through the reviewed topic-semantic aliases used for catalog matching;
  a synthetic bird-topic API test exposed that raw `con chim` labels previously lacked the same
  reviewed semantic hints as the English `bird` label.

## Qwen runtime

- Lightning vision, localization, and child-preference classification share one persistent,
  killable Qwen subprocess and serialize inference through the existing Qwen request lock. This
  avoids loading a separate Qwen instance for the preference classifier. Timeout/runtime failure
  terminates the process; service shutdown explicitly releases it.
- A multiprocessing regression test confirms successive calls reuse one worker PID and one
  monotonically increasing worker generation counter. This is a lifecycle test with a synthetic
  worker, not an L4/GPU latency or memory benchmark.

## Catalog audit

Command: `backend\.venv\Scripts\python.exe backend\tools\audit_child_profile_catalog.py`
with `PYTHONPATH=backend/src;.`.

| Measure | Result |
|---|---:|
| Semantic profiles / templates | 300 / 300 |
| Review-eligible profiles mapped to a template | 300 / 300 |
| Scene concepts / learning objectives | 33 / 20 |
| Readiness metadata `AUTHORED` / `UNSPECIFIED` | 100 / 200 |
| Templates with readiness IDs | 100 / 300 |
| Templates with materials / minimum supervision | 300 / 300 |
| Templates with activity-history prerequisites | 14 |
| Static upper-bound survivors with readiness observed, all materials available, direct adult supervision, and no unobserved activity-history prerequisite | 85 |
| Static survivors if child readiness is unobserved | 17 |

The post-gate counts are upper bounds by concept and age band, not actual runtime recommendations:
the audit assumes a band midpoint, direct adult supervision, all materials available, and (for the
85 count) all authored readiness observed. The 17 unobserved-readiness survivors are activities whose
readiness metadata is authored with no readiness IDs, so those activities require no child-readiness
answer; activities with an authored readiness prerequisite are not counted unless it is observed.
The audit does not evaluate scene matching or activity-specific safety context. No readiness criteria
or activities were added because the `UNSPECIFIED` records need authoritative source/reviewer evidence;
increasing the catalog count would not fix that gap.

## Verification still required

- Completed local checks on 2026-09-29:
  - `PYTHONPATH=backend/src;.` from the repository root, then `pytest backend/tests/unit backend/tests/contract --basetemp=<OS temp> -p no:cacheprovider --tb=short -q` — all tests passed. Running the same suite with `backend/` as the working directory initially failed seven catalog tests because their fixture loader resolves `backend/data/...` from the repository root; rerunning from the documented root passed.
  - Ruff check over the changed backend modules/tests — passed.
  - `apps/ui-mobile`: `node_modules/.bin/tsc --noEmit` — passed.
  - `apps/ui-mobile`: `npm test` (`validate-ui-copy.mjs`) — passed.
  - `python tools/validate_repository_security.py` — passed; 10,950 publishable files scanned, no absolute machine paths.
  - Catalog audit completed; counts and assumptions are recorded above.
- Android emulator `Pixel_10` (`emulator-5554`) was connected; `com.sketch2life.mobile` was foregrounded, Metro was listening on 8081, and `adb reverse tcp:8081 tcp:8081` was active. The emulator reached the local backend on port 8000 and created a session.
- On the emulator, preference text stayed local while typing; the classification route was invoked only after the explicit AI button. The first local backend process was stale and lacked the new route; after restart, the real Lightning connection closed unexpectedly (`RemoteDisconnected`). The backend now converts this into a sanitized retryable 502, and the mobile UI shows the safe “try again or continue without personalization” message rather than an unreadable response. No raw entered text was logged. A successful live tag classification and the later readiness → final-candidate → Gate B happy path could not be verified while the upstream classifier connection was unavailable.
- The profile inputs now use screen-local draft state rather than updating global app context on every keystroke. A follow-up code review caught and fixed a related UI bug: the explicit AI button had checked only committed profile text, leaving it disabled for a new draft. It now checks the local draft and hides stale tag proposals while either field is being edited.
- Android `gfxinfo` snapshots during the local interaction recorded 152 frames with 75 janky (49.34%), then 227 cumulative frames with 146 janky (64.32%); P95 frame duration was 18–19 ms and the slow-UI-thread counter was 0. A 42-frame `HandleInputStart`→`FrameCompleted` proxy was 18.23 ms, but it is **not** an input-to-paint latency measurement. No pre-change baseline or valid p95 input-event trace was available, so the <100 ms input target is not proven; the emulator’s high cumulative jank requires owner review rather than being presented as a pass.
- The remote Lightning L4 was not accessible for a successful classification latency/GPU-memory check or a Qwen/SAM2 coexistence smoke. Keep FEAT-033 `IN_PROGRESS` until the remote classifier and full Android happy path are verified.
