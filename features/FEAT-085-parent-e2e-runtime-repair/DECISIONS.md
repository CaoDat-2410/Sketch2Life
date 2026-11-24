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

### Verification update — 2026-11-24
DEC-085-05 remains the reporting rule: worker completion or a ready-state screen alone is not playback evidence. For this run, playback was directly observed on Android: the authenticated preview advanced to 0:08 / 0:30 and the frame changed. The run is now recorded as playback PASS, while the candidate remains an unreviewed technical preview. No new video generation was submitted.
