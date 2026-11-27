# FEAT-098: more narration and faster learning video

- **Status:** BUILT_AND_TESTED, two targets missed (plan `plan/PLAN_REV1.md`, approved 2026-11-27 with "Duyệt Rev 1").
  Parts A, B and C done; one video made through the app. Words (97 of 110) and voice share (39% of 45%) are short of
  the target; see `evidence/README.md`. Nothing committed.
- **Opened:** 2026-11-27, from the owner's chat: the children's video can say more, and video creation time must come
  down. Research and plan first.
- **SRS:** FEAT-063 v2.7-draft: BR-24, FR-AI-04, FR-AI-08. No SRS change proposed.
- **Builds on:** FEAT-093 (Modal video pipeline), FEAT-094 (learning video; open owner decisions on scene length
  following the voice and on approving knowledge cards).
- **Records:** `research/VIDEO_RESEARCH.md`, `approvals/TASK_APPROVAL.md`, `status/STATUS.md`, `DECISIONS.md`,
  `evidence/README.md`.

## What changed

| Area | Change |
|---|---|
| Narration | facts per band 5 / 6 / 7; three sentences and 22 to 32 words per scene; one scene may tell two facts |
| Timing | learning scenes are rendered as long as their voice, up to 12 s; later scenes shift |
| Review time | scene pictures are prepared and the renderer loaded while the Parent reads the script (`SKETCH2LIFE_STORY_VIDEO_PREPARE_AHEAD`, on in the local Compose stack) |
| Worker | `natten` installed; prepared pictures kept 2 h on the scratch volume; the warm-up no longer unloads a loaded renderer |
| Options | `conv_vae,small` on by the owner's choice (deploy default; `SKETCH2LIFE_VIDEO_OPTIONS=none` switches off); `fps16` off |
| App flow | the Parent first story asks for the learning script |
| Text filter | listed words are compared with their accents (backend and story writer) |
