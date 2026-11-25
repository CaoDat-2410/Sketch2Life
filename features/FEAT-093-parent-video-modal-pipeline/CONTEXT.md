# FEAT-093 context — Parent video from the child's drawing, end to end on Modal

- Status: PLANNED (awaiting owner approval; see `approvals/TASK_APPROVAL.md`)
- Owner: Product owner
- Goal: the Parent flow ends with a real, playable video that is generated on Modal from the confirmed
  script, the child profile (age), the chosen activity and the child's own drawing, keeping the crayon line
  look, with clear main/secondary subjects, a scenic background and a Vietnamese narration.
- Non-goals: real-child data, production quota/billing adapters, Teacher video, SRS sign-off.
- Dependencies: FEAT-087 (subject roles, staging, keyframe compositor, worker prompt `story-i2v-v8`),
  FEAT-086 (LTX scene prompts), FEAT-092 (story input v3, drawing/activity fixes), FEAT-088 (Modal dev workspace).
- SRS authority: FEAT-063 SRS v2.7-draft only (`docs/context/SRS_AUTHORITY.md`).

## What the owner asked for (chat, 2026-11-25)
1. The video is generated from the script, the child profile, the activity and the child's drawing.
2. Keep the crayon line look of the earlier video, but make roles explicit from the start: main subject and
   secondary subjects. Example: turtle eating a leaf — the leaf must not vanish; it is nibbled away gradually.
3. The script must fit the child's age; the video too.
4. The drawing is on a white page; scenery around the subjects may be added.
5. Storytelling uses speech: Vietnamese narration (TTS) and Whisper.

## Findings that shape this plan (verified in the repository and on the emulator)
- Drawing analysis, activity suggestions and story generation now run on Modal from the app (FEAT-092).
- The app (HEAD) requests video through the T-1a contract: `POST /v1/story-runs/{id}/video-generations`
  (admission, then a job projection, then playback tokens). The backend answers 503 `PROVIDER_UNAVAILABLE`
  because `app.state.story_video_ports` is `None` unless `story_video_adapters=local_test`.
- Even with `local_test`, nothing renders: `FixtureVideoRunner` / `FixtureVideoRenderer` only produce a
  synthetic, undecodable MP4, and nothing schedules the runner in the live API. No Modal renderer exists for T-1a.
- The older Modal-backed path (commit `77635688`, FEAT-081 Rev42 "candidate": router `parent_video_candidates.py`,
  service, repository, `ModalSilentStoryVideoWorker`, app client and `VideoCandidateScreen`) was lost in a merge:
  the router is not mounted, `Settings.parent_video_dev_candidate_enabled` does not exist, the app client calls
  are gone. The backend service, repository and worker adapter still exist and are reusable.
- FEAT-087 implemented offline: recognition v2 (main + 0–3 secondary), roles API and UI, per-scene staging,
  keyframe compositor with SAM masks, LTX end-frame guide, prompt `story-i2v-v8`. Its live validation (M6, M7)
  was blocked for lack of Modal credentials; the Modal dev workspace is now reachable from this machine.
- Narration: `synthesize-vietnamese-narration` (VieNeu) and `transcribe-vietnamese-audio` (Whisper) are
  deployed in `sketch2life-srs23-language-audio-dev`; nothing mixes narration into the video.
- Repository hygiene found on the way: a leftover `parent_story_repository.py.rej`, a test importing a symbol that
  was missing at `HEAD`, v1/v2/v3 story input drift (fixed in FEAT-092).
