# FEAT-085 decisions

## DEC-085-01 — Real synthetic end-to-end only
Use the actual Expo app, backend and deployed Modal workers; do not use a preview harness, fixtures, or fabricated API output.

## DEC-085-02 — Preserve hard gates
A test must use eligible synthetic/development records and configured admission. Do not turn off consent, authorization, safety, schema, or video quota enforcement just to obtain a pass.

## DEC-085-03 — Minimize paid inference retries
Submit a workload once; after a verified fix, retry only that failed workload. Do not repeatedly send unchanged prompts/requests.

## DEC-085-04 — Target the real-Firebase API without disturbing other stacks
The API on `58000` belongs to a different worktree and forces Firebase Auth Emulator mode. The API on `18000` verifies real Firebase tokens but lacks the current registration-completion route, and its DB revision is not in this branch's Alembic graph. Run the current branch API on `18001` with a fresh isolated synthetic database; leave both older API containers and their data volumes intact.

## DEC-085-05 — Report candidate readiness separately from playback
The real Modal video worker completing and the Parent UI displaying “Video đã sẵn sàng” are evidence that inference, candidate collection, and the ready-state API path succeeded. They do not prove the player opened or frames advanced. If emulator playback cannot be observed, record it as NOT VERIFIED and retain the candidate; do not infer playback success from worker completion or submit another generation.

## DEC-085-06 — Preserve staged model and stop only task-used Modal apps
After the successful LTX-2.5 run, stop only the video and language/audio apps used by this task; preserve the pinned model volume and unrelated apps. Verify the exact profile/environment inventory reports those apps stopped with zero tasks.

## DEC-085-07 — Keep 16 KB alignment separate from the HMR fix

Repair the root Parent bundle's Metro helper resolution without changing Expo/RN versions or native ABI. Treat the Android 16 KB native-library alignment notice as a separate compatibility task because it requires checking/rebuilding all affected native libraries, not changing JavaScript bundle conditions. The HMR fix is verified; 16 KB alignment is not claimed as complete.

### Verification update — 2026-11-24
DEC-085-05 remains the reporting rule: worker completion or a ready-state screen alone is not playback evidence. For this run, playback was directly observed on Android: the authenticated preview advanced to 0:08 / 0:30 and the frame changed. The run is now recorded as playback PASS, while the candidate remains an unreviewed technical preview. No new video generation was submitted.

## DEC-085-08 — Provide safe-area context at the Parent app root

`ParentBottomBar` uses `useSafeAreaInsets()`, so the composition root must wrap the Parent app in `SafeAreaProvider`. Keep this as app-shell infrastructure; do not add provider ownership to individual screens or change auth/session behavior. Verified by a successful real synthetic login and authenticated home render on Android on 2026-11-24.

## DEC-085-09 — Keep drawing validation strict and recover from server state

Keep the drawing-understanding V2 box schema and hard geometric validation unchanged. Make the prompt explicit about coordinate order and inequalities, and classify safe box failures precisely without logging model content. On resume, derive whether the one permitted drawing replacement was used from the server's input revision; never reset that rule from local memory. If the local image URI is missing, the Parent can check server status; if a failed analysis has exhausted its replacement, the UI exposes the normal authenticated close/restart action. Do not repeat an accepted Modal call.

## DEC-085-10 — Stop after the diagnosed Modal account-limit rejection

Under Addendum 19, the same synthetic Parent UI run received a second `RESOURCE_EXHAUSTED` with no Modal call ID after the safe diagnostics build. The bounded UI resume was also rejected and the safe classifier returned `ACCOUNT_QUOTA_OR_LIMIT`; Modal function stats report zero accepted inputs and zero containers. Preserve the attached drawing and run, make no more inference requests, and report that the Modal workspace owner must resolve the account/compute limit before E2E work resumes. The user's two successful E2E objective remains open; no script or video may be claimed for this attempt.

## DEC-085-11 — Separate Sandbox notices from Function spawn rejection

The one Addendum 20 Parent UI request was rejected at Modal `Function.spawn` with `ResourceExhaustedError` and no call ID, so no GPU worker started. The UI preserves the selected synthetic drawing and returns an actionable terminal state. Stop further inference under Addendum 20. Treat the CPU Sandbox limits notice as a different feature from this GPU Function invocation; do not claim it caused the rejection. The exact account/compute/rate limit is not exposed by current safe diagnostics. The owner-pasted `BOX_INVALID` log is a separate previously accepted Qwen call and is addressed by strict local prompt/validator improvements; deployment remains unverified.

## DEC-085-12 — Preserve the run when Parent activity catalog is empty

The 2026-11-25 real Parent retry confirmed that an empty Parent-visible Lesson Library is a data precondition: the activity-list API returned HTTP 200 with no selectable items because the isolated DB has zero lesson items/versions. Do not fabricate a selection or write directly into the DB to force story/video. Resume only after a lesson becomes available through the normal publish/share workflow or a separate approved implementation supplies the no-candidate AI fallback. Keep the current run and drawing intact.
