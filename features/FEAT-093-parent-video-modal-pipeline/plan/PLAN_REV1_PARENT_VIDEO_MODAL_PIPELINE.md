# FEAT-093 Plan Rev 1 — Parent video from the child's drawing, end to end on Modal

Status: PLANNED. Not approved. No implementation starts before `approvals/TASK_APPROVAL.md` says APPROVED.
Authority: FEAT-063 SRS v2.7-draft (`docs/context/SRS_AUTHORITY.md`). Open questions are kept in section 12, not guessed.

## 1. Outcome

After the adult confirms the script, the app shows a **playable video** that was generated on Modal from:
the confirmed script (with narration lines and timestamps), the child profile (age band), the chosen
activity, and the child's own drawing. The video keeps the crayon line look, treats **main** and
**secondary** subjects explicitly, shows a scenic crayon-style background instead of a bare white page, and
has a Vietnamese narration track. Nothing reaches the UI until the whole pipeline passes its live checks.

## 2. Decisions taken from the owner's answers (2026-11-25)

| ID | Decision | Source |
|---|---|---|
| D1 | Narration is **TTS only** (VieNeu). **Whisper is not used.** Quality is protected by a stricter script contract and deterministic audio checks (section 7). | owner |
| D2 | The script is written **with dialogue/narration lines and timestamps from the start** (Qwen), so audio and scene timing are planned before any rendering. | owner |
| D3 | Background = AI-generated crayon-style **background plate** per scene, with the child's real subjects composited on top (FEAT-087 compositor). The generator and the method are fixed in section 6. | owner, option 1 |
| D4 | Age fit follows the system's three bands: 36–71, 72–107, 108–120 months (section 5). | owner |
| D5 | The whole pipeline is finished and live-checked **before** it is wired to the UI. | owner |
| D6 | GPU topology on Modal L40S: **two containers for LTX-2.5 scene rendering and one container for scene preparation** (background plate, masks, keyframes). Narration runs on the existing language/audio app. | owner |
| D7 | The product contract stays **T-1a** (`POST /v1/story-runs/{id}/video-generations` → job projection → playback token). The app is not rewritten. The old "candidate" path (commit `77635688`) is **retired**, but its orchestration code is reused. | proposed; owner to confirm |

## 3. Current state (verified)

- App (HEAD) requests video through T-1a. Backend returns 503 `PROVIDER_UNAVAILABLE` because
  `app.state.story_video_ports` is `None` unless `story_video_adapters=local_test` (accept-all admission fixtures).
- Nothing renders in the live API: `FixtureVideoRunner` + `FixtureVideoRenderer` exist for tests (synthetic, undecodable
  MP4) and nothing schedules a runner. There is no Modal renderer for T-1a.
- Reusable, still present: `ParentVideoCandidateService` (source read, manifest, dispatch, reconcile),
  `SqlParentVideoCandidateRepository`, `ModalSilentStoryVideoWorker`, T-1a repository/runner/state machine,
  playback token codec (T-1c), asset metadata writer, FEAT-087 staging, `keyframe_plan`, `keyframe_compositor`,
  `sam_masks`, prompt `story-i2v-v8`, `story_visual_plan`.
- Modal (dev workspace `hieuptse184252`): `generate-video-scene` and `generate-silent-story-video` on L40S with
  `max_containers=1`; `flux_image_app.py` (FLUX.3 klein, license "FLUX Kommunity License v1.0", dev-only) is **not deployed**;
  language/audio app has `synthesize-vietnamese-narration` (VieNeu).
- FEAT-087 live validation (M6, M7) never ran. Nothing has been rendered by LTX with roles/keyframes.

## 4. Target architecture

```
confirm script (adult)
   └─ POST video-generations (T-1a, admission accept-all in local/dev)         [API]
        └─ generation row ACCEPTED  ──────────────────────────────►  video worker process (new, DB-driven)
                                                                       │
 P0 plan        story + roles + staging + age band → VideoPlan v1      │  CPU
 P1 prepare     (scene container, L40S #3, per scene, parallel)         │
                  background plate (FLUX) ─ QC ─┐                        │
                  SAM masks / sprites ───────────┼─► keyframes K(i)     │
 P2 narrate     VieNeu TTS per line (language/audio app) ─ audio QC     │  CPU/L4
 P3 render      LTX-2.5 per scene, N scenes over 2 containers (L40S #1,#2)  │
 P4 assemble    concat scenes, mux narration, loudness normalise (ffmpeg) │  CPU
 P5 validate    technical + consistency + safety checks                 │
 P6 publish     MinIO object, asset metadata, state READY               │
                                                                         ▼
 app polls run (job projection) → playback token → stream               [existing T-1c]
```

Scene work is independent per scene, so wall time ≈ P1 + P2 (parallel) + ceil(N/2) × LTX scene time + P4–P6.
Per-scene LTX time and the memory headroom of "SAM + LTX in one container" are **measured in M0** before the
topology is frozen (the owner's D6 is the starting hypothesis, not an assumption of speed).

## 5. Age bands (D4)

Proposed values. Owner confirms in M0; the contract tests read them from one table (`video_age_profile.py`).

| Band (months) | Scenes | Seconds per scene | Narration per scene | Dialogue lines | Subjects | Plot |
|---|---|---|---|---|---|---|
| 36–71 | 4 | 4 | 1 sentence, ≤ 9 words | ≤ 1, ≤ 5 words | 1 main + ≤ 1 secondary | one simple action per scene, concrete words, no abstract ideas |
| 72–107 | 5 | 4–5 | ≤ 14 words | ≤ 2 | 1 main + ≤ 2 secondary | cause and effect allowed |
| 108–120 | 6 | 5 | ≤ 20 words | ≤ 3 | 1 main + ≤ 3 secondary | short problem and solution arc |

Existing limits (scene count, durations, staging caps) are reconciled with this table in M0; any conflict is
reported, not silently changed.

## 6. Background plates (D3)

- **Generator:** FLUX.3 klein (`flux_image_app.py`), run in the **scene container** (L40S #3). Qwen writes a short English
  `background_prompt` per scene (place, time of day, objects) under a fixed crayon style prefix; the child's subjects are never
  described in it, so the model does not redraw them.
- **Compositing:** the child's real subjects (SAM-masked sprites from the original drawing, FEAT-087) are pasted onto the plate at
  the planned boxes. The child's pixels are never regenerated (requirement A4 of FEAT-087: sprite pixel-identical to the drawing).
- **Consistency:** one style seed and palette per video; scenes of one video share the plate family.
- **QC per plate (automatic):** no text/letters, no faces or people unless the script has them, no overlap with the subject boxes
  (a plate region under a subject is flattened to paper tone), Qwen-VL yes/no safety and style check; on failure retry twice then
  fall back to the plain paper plate and mark the scene `background=PAPER`.
- **Licence:** "FLUX Kommunity License v1.0" is recorded as an open question (section 12); it is acceptable for the dev workspace only.

## 7. Script, dialogue, timestamps and narration (D1, D2)

- **Story JSON v-next** (`sketch2life.story-timeline.v1`): per scene `{index, start_ms, end_ms, narration:{text,start_ms,end_ms},
  dialogue:[{speaker_ref,text,start_ms,end_ms}], action, interactions:[…], background_prompt, subjects:[ids]}`. Public story keys used by
  the app (title, story.opening/middle/ending, scenes[].title/action/narration) stay compatible.
- **Qwen produces the timeline** under the age band: word-count caps, one action per scene, total duration inside the band. The parser
  rejects a timeline that overlaps, has gaps beyond tolerance, exceeds caps, or uses banned content (same gate family as the
  activity parser: dangling endings, non-Latin letters, PII).
- **Narration QC without Whisper** (deterministic): VieNeu renders each line; checks = non-empty audio, sample rate/channels, no clipping,
  leading/trailing silence bounds, **speech rate** (characters per second inside a band-specific range), duration fits the scene window
  (otherwise: shorten by re-asking Qwen once, else stretch the scene within ±15 %, else fail the generation), text lint for numerals,
  abbreviations and foreign words that the TTS reads badly (normalised before synthesis, listed in the evidence).
- **Human gate:** the adult already reviews the script; the finished video (with sound) is the second review. Nothing is published to
  other users by this feature.

## 8. Roles and interactions (FEAT-087 wired into rendering)

- Main/secondary roles come from recognition v2 and the adult's confirmed edits; they are frozen in the plan.
- **Interaction states** make "turtle eats the leaf" correct: the secondary sprite persists across scenes; verbs such as eat/pick/carry map
  to a state ladder (intact → bitten 25 % → 50 % → 75 % → gone only in the last scene when the script says so). The compositor applies
  the ladder with the SAM mask (progressive erosion at the bite side), and LTX receives the keyframe plus the end-frame guide so the
  leaf is never replaced by a different object.
- Acceptance uses the turtle-and-leaf drawing as the golden case (section 10).

## 9. Backend work packages

1. **`VideoPlan` builder** (pure domain): inputs story timeline, roles, staging, age band; output scene list, keyframe plan, audio plan.
2. **`ModalVideoRenderer`** implementing `VideoRenderPort`, plus a **video worker process** (new compose service, DB-driven; reuses the
   sweep worker pattern) that advances `ACCEPTED → QUEUED → GENERATING → TECHNICAL_VALIDATING → SAFETY_VALIDATING → READY/FAILED`.
   It never runs inside the request. Idempotent per generation id; resumable after a restart; cancellation honoured; hard timeouts per phase;
   scratch cleanup; no provider text in client responses.
3. **Source reader** (read-only): drawing asset, confirmed story revision, roles, activity snapshot, child age band from the profile.
4. **Scene preparation function** (new Modal function, L40S #3): plate + masks + keyframes per scene; output to the scratch volume.
5. **LTX function** `generate-video-scene` with `max_containers=2`; the existing `generate-silent-story-video` is kept or retired by decision in M0.
6. **Narration function** call into the language/audio app, per line, plus the audio QC module.
7. **Assembler** (ffmpeg): concat, mux, loudness normalise, faststart; output MP4 stored under the existing key scheme.
8. **Validation:** technical (decodable, duration, resolution, audio track), consistency (subject present in every scene by mask match),
   safety (frame-sample classification by Qwen-VL; blocked → `SAFETY_BLOCKED` with codes only).
9. **Config:** `story_video_adapters` gets a third value `modal_dev` (refused outside local/test), the admission fixtures stay accept-all in dev.
10. **Retire** the candidate router/service/settings paths after the new flow passes (no dead second video API).
11. **Hygiene:** delete `parent_story_repository.py.rej` after applying or dropping its FEAT-087 hunks on purpose; fix the test that imports a
    missing symbol; add a repository guard test that fails when a router listed in the SRS operations is not mounted.

## 10. Milestones and acceptance criteria

| M | Work | Acceptance (all measurable) | Evidence |
|---|---|---|---|
| M0 | Spikes and freeze: LTX scene time on L40S; memory of SAM + LTX; FLUX background on L40S; TTS rate; concurrency allowed by the Modal workspace; reconcile limits; confirm section 5 and decisions | measured numbers recorded; topology decision recorded (ADR) | `evidence/M0_*.md` |
| M1 | `VideoPlan` + timeline contract + age profile + parser | unit tests: caps per band, overlap/gap rules, golden turtle plan; 100 % branch coverage of the parser rules | tests |
| M2 | Story prompt/parser v-next (timeline, dialogue) | 20 synthetic drawings × 3 bands pass the parser ≥ 95 % first try; failures give safe codes; no banned content | `evidence/M2_*` |
| M3 | Scene preparation function (plates, masks, keyframes, interaction ladder) | turtle-leaf keyframes show leaf bitten 25/50/75/gone; sprite pixels identical to the drawing (hash check); plate QC rules enforced | images + metrics |
| M4 | Narration + audio QC + timing fit | all lines pass QC; zero scenes over/under window beyond tolerance; speech rate in band | audio files + report |
| M5 | LTX rendering over 2 containers + assembler | 3 videos decode; scene boundaries and audio sync within 100 ms; subjects present in every scene; crayon lines preserved (line-width/edge metric vs drawing) | videos + metrics |
| M6 | `ModalVideoRenderer`, worker process, state machine, storage, tokens | integration tests on Postgres/MinIO: happy path, restart mid-job, cancel, timeout, duplicate request, storage failure; live API run produces READY | tests + logs |
| M7 | Safety and technical validation | blocked sample is blocked; valid sample passes; codes only in responses | tests |
| M8 | Live run through the real app flow on the emulator, three drawings (turtle+leaf, chicken, one with two secondaries), one per age band | start to finish without manual DB or Modal edits; video plays with sound; stage list shows real progress; failure path shows a clear message | `evidence/M8_*` recordings |
| M9 | Cost and time report; cleanup; retire candidate path | per-video GPU seconds and wall time reported; no orphan Modal apps/objects; candidate code removed | report |

Order: M0 → M1 → M2 → (M3 ∥ M4) → M5 → M6 → M7 → M8 → M9. Nothing is shown in the UI before M8 (D5), but each milestone is verified through
the API or scripts.

## 11. Budget, safety and rules

- **GPU budget (proposal, owner confirms):** at most 40 scene renders and 12 complete videos across M0–M8; any run above 2× the measured
  per-video estimate is stopped. Models stay in the dev workspace volume; no secret leaves it.
- Synthetic drawings only; no real-child data; Firebase Authentication only; mobile holds no Modal/S3 credentials; originals and provenance are
  preserved and derived keyframes never replace the source drawing.
- Deploys to Modal use the documented commands and the local profile; each deploy is recorded in `evidence/`.
- `python tools/validate_repository_security.py` must be clean for the files this feature touches before any commit.

## 12. Risks and open questions

| # | Item | Mitigation / question |
|---|---|---|
| R1 | SAM + LTX memory in one L40S, or LTX end-guide quality, may fail (FEAT-087 M6 never ran) | M0 spike; fall back to separate SAM step in the scene container |
| R2 | Workspace may cap concurrent GPUs below 3 | M0 check; sequence scene preparation before LTX if capped |
| R3 | LTX can still deform subjects | guide strength tests, mask-match consistency check, fail closed with a clear message |
| R4 | FLUX.3 klein licence ("FLUX Kommunity") may not allow product use | **Open question O1**: dev only for now; alternative generator decided before any release |
| R5 | VieNeu may mispronounce names/numbers | text normaliser + QC; O2: which voice/speed for each band? |
| R6 | Total latency too long for a parent waiting | M0 measures; the app already shows a stage list and lets the adult leave the screen |
| O3 | Is an audio track allowed in the SRS video requirements, or is "silent video" a product rule? | check SRS before M4; if silent is mandated, narration becomes a separate track |
| O4 | Should the adult be able to pick the voice or turn narration off? | default on, no picker in this feature |
| O5 | Do secondary-subject eat/pick interactions need adult confirmation in the review step? | default: derived from the confirmed script, shown in the existing review text |

## 13. Rollback

Feature flag `story_video_adapters` returns to `unconfigured` (503 as today) or `local_test` (fixtures). No schema change is irreversible:
new tables, if any, are additive. The candidate path is removed only in M9 after M8 passes.
