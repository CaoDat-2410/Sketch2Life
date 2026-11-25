# FEAT-093 Plan Rev 2 — Parent video from the child's drawing, end to end on Modal

Status: PLANNED, **not approved**. Supersedes `PLAN_REV1_...` (kept for history). No implementation, deploy or GPU run
starts before `approvals/TASK_APPROVAL.md` says APPROVED for this revision.
Authority: FEAT-063 SRS v2.7-draft (`docs/context/SRS_AUTHORITY.md`). Open questions are listed in section 14, not guessed.

What changed from Rev 1 (owner feedback, 2026-11-25): only **two** GPU containers; the turtle/leaf case is **one example, not the
design** (general interaction model); the **recognition step is reworked** (main/secondary choice, ambiguity); **script and activity
prompts/formats** get their own specification and evaluation; a **"while you wait" outdoor-activity section and a floating status chip**
are added; the **UI changes and a UI test script** are specified in detail.

## 1. Outcome

After the adult confirms the script, the app shows a playable video generated on Modal from the confirmed script (with narration and
timestamps), the child profile (age band), the chosen activity and the child's drawing. It keeps the crayon look, treats main and secondary
subjects explicitly, shows a crayon-style scenic background, and has a Vietnamese narration. While the video is generated (minutes), the
child can do an outdoor activity, and a floating chip tells the adult when the video is ready. Nothing is wired to the UI until the backend
pipeline passes its live checks (D5); the UI work and its tests are in section 11.

## 2. Decisions

| ID | Decision | Source |
|---|---|---|
| D1 | Narration is **TTS only** (VieNeu). **No Whisper.** Quality comes from a strict timeline contract and deterministic audio checks (section 8). | owner |
| D2 | The script is written **with narration/dialogue lines and timestamps from the start**. | owner |
| D3 | Background = AI-generated crayon-style plate per scene, the child's real subjects composited on top. Generator and method in section 7. | owner |
| D4 | Age fit follows three bands: 36–71, 72–107, 108–120 months (section 6). | owner |
| D5 | The whole backend pipeline is finished and live-checked before UI wiring. | owner |
| D6 | **Exactly two GPU containers (L40S):** **C1 = LTX-2.5 only**; **C2 = everything else** (Qwen text/vision, scene preparation with FLUX plates and SAM masks, TTS). Light CPU work (compositing, ffmpeg) runs in the API worker process. | owner (corrected) |
| D7 | Product contract stays T-1a (`POST /v1/story-runs/{id}/video-generations` → job projection → playback token); the old "candidate" path is retired after the new flow passes; its orchestration code is reused. | proposed |
| D8 | Recognition output keeps **all** detected objects with boxes and a proposed role; the adult confirms roles; ambiguous cases require an explicit choice (section 5). | owner (corrected) |
| D9 | Interactions (eat, pick, carry, chase…) are a **general state-transition model**, not a turtle/leaf special case (section 9). | owner (corrected) |
| D10 | While the video is generated, the app offers the chosen outdoor activity and shows a floating status chip (section 11). | owner |

## 3. Verified current state

- Drawing analysis, activity suggestions and story generation run on Modal from the app (FEAT-092): 190–220 s, 280–450 s, 290 s.
- **Recognition output is reduced to one subject.** The Modal worker returns `main_subject`, `secondary_subjects` with 20×20 boxes, `confidence`
  (seen: a main chicken plus two secondary objects), but the stored understanding keeps only `candidate_subject`, `visible_features`, `decision`
  and `confidence`; boxes and secondaries are dropped by `candidate_from_result`, so the roles UI never receives anything and no keyframe input
  exists. `confidence` was 1.0 on all four live runs (over-confident or not calibrated).
- A leftover `parent_story_repository.py.rej` holds FEAT-087 hunks (`apply_subject_roles`, `approved_subjects`, `relabel_main_subject`) that were
  never applied on `dev`.
- Activity generation is slow (4.6 tokens/s; 1,700–2,000 tokens ≈ 5–7 min) and was rejected once by a text gate for a dangling word; it now drafts 4
  and keeps up to 3 (FEAT-092).
- T-1a returns 503 `PROVIDER_UNAVAILABLE` (no adapters); `FixtureVideoRunner` renders a synthetic non-decodable MP4 and nothing schedules a runner.
- Reusable: candidate service/repository, `ModalSilentStoryVideoWorker`, T-1a state machine, playback tokens, asset metadata, FEAT-087 staging,
  `keyframe_plan`, `keyframe_compositor`, `sam_masks`, prompt `story-i2v-v8`, `story_visual_plan`.
- Modal dev workspace: video app has L40S `generate-video-scene` and `generate-silent-story-video` (`max_containers=1`); `flux_image_app.py`
  (FLUX.3 klein) not deployed; the shared `qwen-worker` already serves several workloads from one warm L40S (pattern for C2).
- App shell: `VideoScreen` (T-1a panel, player, reasons), `UnderstandingScreen` (roles UI present, empty today), `StoryScreen`, `ActivityScreen`;
  no notification or haptics dependency in `package.json`; bottom tab bar exists.

## 4. Target architecture with two containers

```
adult confirms script ──► POST video-generations (T-1a admission) ──► generation ACCEPTED
                                                                         │
                          video worker process (new, DB-driven, CPU) ◄───┘
   P0 plan        VideoPlan from timeline + roles + age band                                   (CPU)
   P1 prepare     per scene: background plate (FLUX), SAM masks, keyframes, interaction states   (C2, L40S)
   P2 narrate     VieNeu per line + audio QC                                                    (C2 or CPU)
   P3 render      LTX-2.5 per scene, strictly one scene at a time                               (C1, L40S)
   P4 assemble    concat, mux narration, loudness, faststart (ffmpeg)                           (CPU)
   P5 validate    technical + consistency + safety                                              (C2 for VL checks)
   P6 publish     MinIO object + asset metadata → READY; token/stream by existing T-1c
```

- **Pipelining replaces parallel LTX:** C1 renders scene *i* while C2 prepares scene *i+1*. Wall time ≈ P0 + P1(first scene) + N × LTX scene time +
  P4–P6. The per-scene LTX time is measured in M0; the number of scenes per band (section 6) is adjusted to keep wall time acceptable.
- **C2 memory:** Qwen3.8-27B-FP8, FLUX.3 klein, SAM 2.1 small and VieNeu may not fit one 48 GB L40S together. C2 gets a **model residency manager**
  (one heavy model resident at a time, lazy load/unload, measured swap cost). Interactive workloads (recognition, activities, story) keep priority
  and a video job never starts a swap while an interactive request is queued. If M0 shows the swap cost is unacceptable, the fallback is moving
  VieNeu and SAM to CPU, and only then asking the owner about a third container.
- C1 never runs anything but LTX; it can stay cold (`min_containers=0`) with a measured cold-start in the ETA.

## 5. Recognition rework (new track R)

Goal: every drawing yields a **list of detected subjects with a proposed role**, and the adult confirms or fixes it before the story is written.

**R1. Keep the data.** Persist `understanding_schema v2`: `main_subject`, `secondary_subjects[]`, boxes (20×20 grid and pixel boxes), features,
facing, per-subject confidence. Backfill nothing for older runs (they stay single-subject). Apply the `.rej` hunks on purpose (roles API, approved
subjects) and delete the file.

**R2. Role proposal rule (deterministic, explainable).** Each subject gets a score; the highest is the proposed main subject.

| Signal | Weight | Meaning |
|---|---|---|
| Can act (living or character) | 0.35 | animals, people, fantasy beings, vehicles with a face; plain objects/scenery score 0 |
| Area share of the drawing | 0.25 | box area / page area, capped |
| Centrality | 0.15 | distance of the box centre to the page centre |
| Match with adult intent | 0.20 | label or synonyms match the typed idea, the topic card or the intended subject |
| Completeness | 0.05 | box not cut by the page edge |

Scenery (sun, grass, ground, frame) is `excluded` by a label/size rule unless the adult adds it. Up to 3 secondary subjects are kept by score.

**R3. Ambiguity.** If the top two scores differ by < 0.10, or two subjects can both act, the proposal is flagged `needs_choice`. The UI then
**requires an explicit choice** of the main subject before "Xác nhận" is enabled. No silent guess.

**R4. Meaning of roles.** *Main* = the agent that performs the story's actions. *Secondary* = something the main subject interacts with or that
shares the scene. *Excluded* = not used. One main only; a swap is a single tap (`Đặt làm chủ thể chính`).

**R5. Confidence.** Replace the single self-reported number by a calibrated display: model confidence is shown only together with the label list;
the 4 live runs at 1.0 are investigated in M0 (prompt, enum, over-confidence) and the screen shows a banded label ("Rất chắc / Cần xem lại") with a
threshold from the eval set.

**R6. Evaluation.** 30 synthetic drawings (single subject, two animals, animal + food, vehicle + person, scenery-heavy, tiny subject, cropped subject,
imaginary creature, text on the page). Metrics: main-subject accuracy ≥ 90 %, `needs_choice` precision, box IoU ≥ 0.5 on ≥ 85 % of subjects,
scenery wrongly kept as secondary ≤ 5 %.

## 6. Age bands (D4)

Proposed; the owner confirms in M0; one table in code (`video_age_profile.py`), read by the story parser, the plan builder and tests.

| Band (months) | Scenes | Seconds per scene | Narration per scene | Dialogue lines | Subjects | Plot |
|---|---|---|---|---|---|---|
| 36–71 | 4 | 4 | 1 sentence, ≤ 9 words | ≤ 1, ≤ 5 words | 1 main + ≤ 1 secondary | one simple action per scene, concrete words |
| 72–107 | 5 | 4–5 | ≤ 14 words | ≤ 2 | 1 main + ≤ 2 secondary | cause and effect |
| 108–120 | 6 | 5 | ≤ 20 words | ≤ 3 | 1 main + ≤ 3 secondary | short problem and solution |

Scene counts may shrink if M0 shows the wall time with one LTX container is too long; the owner decides, the table is the single place to change.

## 7. Background plates (D3)

- Generator: **FLUX.3 klein** (`flux_image_app.py`) inside C2. Qwen writes a short English `background_prompt` per scene (place, time, objects) under a fixed
  crayon-style prefix and never names the child's subjects, so the model does not redraw them.
- Method: SAM-masked sprites of the child's real subjects are composited on the plate at the planned boxes (FEAT-087 compositor). The child's pixels are
  never regenerated (sprite hash equals the drawing). One style seed and palette per video.
- Per-plate QC: no text/letters, no unplanned people or faces, subject regions flattened to paper tone, Qwen-VL style/safety yes/no. On failure retry
  twice, then fall back to the plain paper plate and mark the scene `background=PAPER` (visible in the evidence, not an error).
- Licence "FLUX Kommunity License v1.0": open question O1; allowed for the dev workspace only.

## 8. Script, activity prompts and formats (new track S) — narration QC

**S1. One "format card" per AI workload** (doc + code constants + tests): inputs, system prompt, user prompt template, output JSON schema (LMFE
constrained), validators with safe codes, token budget, failure handling, evaluation set. Workloads: drawing analysis, activity suggestion,
story timeline, background prompt, rewrite.

**S2. Story timeline** `sketch2life.story-timeline.v1`: per scene `{index, start_ms, end_ms, narration{text,start_ms,end_ms}, dialogue[{speaker_ref,text,start_ms,end_ms}],
action, interactions[], background_prompt, subjects[]}`. Public keys used today (title, opening/middle/ending, scenes[]) stay compatible.
Prompt rules: age band table injected as numbers; vocabulary limits (common words, no abstractions for the youngest band); the activity's objective and steps
appear as story events; the adult's idea is honoured; no brand/violence/scary content; every sentence ends in a complete Vietnamese word.
Parser rejects overlaps, gaps, caps, banned content, dangling endings, non-Latin letters, PII.

**S3. Activity generation** (outdoor): same format card; each activity has place, materials, 3 steps, an observation and a safety note, checked against the age band
and the recognised subjects; 4 drafted, ≤ 3 kept after the quality gates (already implemented). Speed target: ≤ 3 min median by shortening the schema fields and
profiling decoding (M0); it is a UX requirement because the adult waits.

**S4. Evaluation harness:** 30 drawings × 3 bands run offline against stored model outputs plus a live subset; automatic scores (parse pass, caps, vocabulary
band, banned list) and a human rubric (age fit, coherence, uses activity, uses roles, tone) with pass thresholds in the milestone table.

**S5. Narration QC without Whisper (deterministic):** non-empty audio, sample rate/channels, no clipping, silence bounds, speech rate (characters/second in a
per-band range), line fits its scene window (else Qwen shortens once, else scene stretch ≤ ±15 %, else the generation fails), text normaliser for numerals,
abbreviations and foreign words before synthesis. The adult hears the result in the finished video (second review).

## 9. Interactions and roles in rendering (general, D9)

Interactions are typed by **effect on the secondary subject**, so any verb maps to a handler:

| Effect type | Examples | Rendering rule |
|---|---|---|
| Consume (reduce) | eat, drink, nibble | state ladder 100 → 75 → 50 → 25 → gone on the mask; gone only when the script says finished |
| Transfer | pick up, carry, give | sprite moves with the main subject's box; never duplicated |
| Contact (no change) | pet, hug, look at, follow | sprite persists, relative positions change |
| Transform/appear | grow, open, light up | cross-fade between two planned states, never a new drawing |
| Move away | chase, run, fly | sprite path planned across keyframes |

The turtle-and-leaf drawing is one golden case in a set of at least six (consume, transfer, contact, chase, two secondary subjects, scenery-heavy). A secondary
subject never silently disappears; the consistency check (mask match in every scene) fails the scene otherwise.

## 10. Backend work packages

1. Persist recognition v2, apply roles API hunks, role scoring and `needs_choice` (track R).
2. Story timeline contract, age profile, parser, prompts, format cards, eval harness (track S).
3. `VideoPlan` builder (pure domain).
4. `ModalVideoRenderer` + **video worker process** (new compose service, DB-driven, resumable, cancel-aware, per-phase timeouts, scratch cleanup, no provider text in responses).
5. C2 extension: `utility-worker` entry in the language/audio app (scene preparation, TTS, VL checks) with the residency manager; C1: `generate-video-scene` unchanged apart from inputs.
6. Source reader (read-only), assembler (ffmpeg), validators (technical, consistency, safety), config `story_video_adapters=modal_dev` (local/test only).
7. Retire the candidate router/service/settings; delete the `.rej`; fix the test importing a missing symbol; add a guard test that fails when an SRS operation has no mounted route.
8. Job projection: stable `stage` codes for the app (`PLANNING`, `PREPARING_SCENES`, `RENDERING`, `NARRATING`, `ASSEMBLING`, `CHECKING`) with `scene_index/scene_count`, plus `eta_seconds` (measured median).

## 11. UI changes and UI test script

### 11.1 Changes by screen

| Screen / file | Change |
|---|---|
| `UnderstandingScreen.tsx` | Show detected subjects as cards with a crop thumbnail (from the box), name field, role selector `Chính / Phụ / Không dùng`; exactly one `Chính`; when `needs_choice` the primary button is disabled with the hint "Chọn nhân vật chính để tiếp tục"; scenery listed as `Không dùng` by default; confidence shown as a banded label. |
| `StoryScreen.tsx` | Show the age band chip ("Phù hợp 3–5 tuổi"), per scene: narration text, dialogue lines and the time window; keep rewrite/confirm. |
| `VideoScreen.tsx` | Replace the generic panel by a **real stage list** (6 stages with a progress bar, scene `2/4`, ETA); add a **"Trong lúc chờ" section** (below); keep player (audio on, `playsInSilentModeIOS`), reasons, unsuitable, complete. Allow leaving the screen while generating. |
| New `WhileYouWaitSection.tsx` | The chosen outdoor activity as a checklist (materials, 3 steps, observation, safety), "Bé đã làm xong" toggle per step (local state), a short "Hoạt động khác" list from the other drafts, supervision reminder. |
| New `VideoStatusChip.tsx` (in the app shell, above the bottom bar) | Floating chip visible on every main tab while a video job exists: `Đang tạo video · Cảnh 2/4` with a small progress ring; turns green `Video sẵn sàng · Xem` on READY, red `Chưa tạo được · Xem` on failure; tap opens the video step; dismissible after READY is viewed. |
| `useParentController` / platform controller | Video job polling continues across steps and tabs (foreground only, existing backoff); exposes `videoChip` state; survives app restart by reading the active run. |
| `ParentBottomBar` | Badge dot on the "Câu chuyện"/history tab when the video is ready and not yet viewed. |
| Copy and types | Stage labels, error messages by safe code, age band label; `ParentVideoGenerationStateV1` stages extended. |
| Dependencies | **None added.** Push notification when the app is closed needs `expo-notifications` (native change): open question O6; default is in-app chip + badge only. |

### 11.2 Automated UI-level tests (before the live run)

- vitest component tests: role selector (one main, ambiguity gate), stage list rendering for each stage, chip states (idle/working/ready/failed), wait section checklist.
- vitest controller tests: polling continues when the step changes, chip state after READY, restart restore.
- `npm run typecheck` and `npm test` clean for touched files.

### 11.3 Manual/emulator script (adb-mcp on `emulator-5554`, evidence = screenshots + UI dumps)

Data: synthetic crayon drawings generated by the project script (set A: single animal; B: animal + food; C: two animals; D: scenery-heavy; E: tiny subject).

| ID | Steps | Expected |
|---|---|---|
| U1 | Sign in (owner does it), pick profile Demo, start a topic session, choose drawing A | analysis finishes; one main subject, scenery `Không dùng`, **Xác nhận** enabled |
| U2 | Drawing C (two animals) | `needs_choice`: **Xác nhận** disabled until one is chosen; choosing sets roles; swap works with one tap |
| U3 | Drawing B | main = animal, food = secondary; rename the secondary; toggle to `Không dùng` and back |
| U4 | Confirm roles → activities → select one → context → story | story shows age chip, scenes with narration/dialogue and times; text fits the age band |
| U5 | Confirm story → start video | VideoScreen shows stage list and ETA; **Trong lúc chờ** shows the chosen activity |
| U6 | During generation tap back to Home, then other tabs | floating chip stays, text and progress update; tapping returns to the video step |
| U7 | Tick activity steps while waiting | state persists when leaving and returning to the screen |
| U8 | Background the app 60 s, return | polling resumes, stage updated, no duplicate request (check API log) |
| U9 | Force-stop the app mid-job, relaunch, sign in | active run restored, chip shows the running job |
| U10 | Wait for READY | chip turns green `Video sẵn sàng`, tab badge appears; open → video plays **with sound**, duration matches the plan |
| U11 | Check content for set A, B, D | crayon lines preserved, secondary subject still present in each scene, background plate visible or paper fallback noted |
| U12 | Regenerate with a reason; mark unsuitable | reason required; quota text correct; chip resets |
| U13 | Failure injection (stop Modal app, or oversize drawing) | chip red, clear Vietnamese message, no endless spinner, retry allowed per policy |
| U14 | Double tap **Tạo video**, rotate device, toggle airplane mode during polling | one generation only; recovers when the network returns |
| U15 | Complete the session | run closes; chip gone; history shows the finished item |

Each case records: build id, API/Modal revision, screenshots, API log excerpt, pass/fail, and the video file hash for U10/U11.

## 12. Milestones and acceptance

| M | Work | Acceptance | Evidence |
|---|---|---|---|
| M0 | Spikes and freeze: LTX time per scene; C2 memory and swap cost (Qwen + FLUX + SAM + TTS); activity decoding speed; confidence over-1.0; Modal concurrency; reconcile existing limits; owner confirms sections 6 and 14 | numbers recorded; ADR for two-container topology and scene counts | `evidence/M0_*.md` |
| M1 | Track R backend: recognition v2 stored, roles API, scoring, `needs_choice`; eval set R6 | R6 metrics met; contract tests; `.rej` removed | tests + report |
| M2 | Track R UI: `UnderstandingScreen` changes | vitest passes; U1–U3 pass on emulator | screenshots |
| M3 | Track S: timeline contract, age profile, prompts, format cards, parser, eval S4 | parse pass ≥ 95 % first try on 90 runs; human rubric ≥ 4/5 mean on 20 samples; safe codes only | `evidence/M3_*` |
| M4 | Activity generation speed and quality | median ≤ 3 min on C2; gate pass ≥ 95 % | timings |
| M5 | Scene preparation (plates, masks, keyframes, interaction handlers) on C2 | six golden interactions pass the consistency check; sprite hash equals the drawing; plate QC enforced | images + metrics |
| M6 | Narration + QC + timing fit | all lines pass S5; no scene outside tolerance | audio + report |
| M7 | LTX rendering on C1 with pipelining + assembler | 3 videos decode; audio sync ≤ 100 ms; subject present in every scene; line-style metric vs drawing within threshold; wall time ≤ the M0 estimate × 1.2 | videos + metrics |
| M8 | `ModalVideoRenderer`, worker, state machine, storage, validation | integration tests (Postgres/MinIO): happy path, restart mid-job, cancel, timeout, duplicate request, storage failure; blocked sample blocked | tests + logs |
| M9 | UI: video stage list, wait section, chip, badge, story timeline view | 11.2 tests pass | vitest |
| M10 | Full emulator run U1–U15 on sets A–E | all pass or documented defects; no manual DB/Modal edit | `evidence/M10_*` |
| M11 | Cost/time report, cleanup, retire candidate path, docs | per-video GPU seconds and wall time; no orphan Modal apps/objects | report |

Order: M0 → M1 → M2 → M3 → M4 → (M5 ∥ M6) → M7 → M8 → M9 → M10 → M11. The recognition track (M1–M2) comes first because roles drive every later step.

## 13. Budget, safety, rules

- GPU budget (owner confirms): at most 40 scene renders and 12 full videos across M0–M10; a run above 2× the measured estimate is stopped.
- Synthetic drawings only; no real-child data; Firebase Authentication only; mobile holds no Modal/S3 credentials; originals and provenance preserved.
- Deploys use the documented commands and local profile and are recorded; `python tools/validate_repository_security.py` clean for touched files before any commit.
- Rollback: `story_video_adapters` back to `unconfigured` or `local_test`; schema changes additive; candidate path removed only after M10.

## 14. Risks and open questions

| # | Item | Mitigation / question |
|---|---|---|
| R1 | C2 memory with Qwen + FLUX + SAM + TTS; swap latency | residency manager; M0 measurement; fallback CPU for SAM/TTS; third container only with owner approval |
| R2 | One LTX container makes long videos slow | pipelining; scene counts per band tunable; ETA shown; wait section |
| R3 | LTX may deform subjects; end-guide quality unverified (FEAT-087 M6 never ran) | consistency check, fail closed with a clear message |
| R4 | Recognition errors on messy drawings | eval set, explicit adult confirmation, ambiguity gate |
| R5 | Activity/story generation latency (4.6 tok/s) | shorter schemas, profiling, token budgets, progress UI |
| O1 | FLUX.3 klein licence for product use | dev only now; decide before release |
| O2 | TTS voice and speed per band | default one voice; owner listens in M6 |
| O3 | SRS: is an audio track allowed, or is "silent video" mandated? | check before M6 |
| O4 | Voice picker / narration off switch | none in this feature |
| O5 | Adult confirmation of derived interactions | shown in the script review text, no extra step |
| O6 | Push notification when the app is closed needs `expo-notifications` (native rebuild) | default: in-app chip and badge only |
| O7 | Should "Bé đã làm xong" be stored on the server (progress for the adult/teacher)? | default: local only |

## 15. Amendment A (2026-11-25) — owner answers to O1, O3, O6, O7; captions

### 15.1 Answers recorded

| Item | Owner answer | Effect on the plan |
|---|---|---|
| O1 | Hugging Face shows "Gated model — You have been granted access" for the owner's account (the screenshot does not name the model; assumed FLUX.3 klein). | **Access** is resolved. **Prerequisite P1:** the Modal download job needs a Hugging Face read token stored as a *Modal Secret* created by the owner; the token never enters the repository, chat, logs or evidence. Licence terms for product use stay recorded as "dev workspace only" until the owner states otherwise. |
| O3 | The parent chooses whether to hear the narration. **Closed captions at the bottom must be exact with the video.** | Audio is optional per parent; captions are a first-class, frame-accurate track (15.2). |
| O6 | Yes, add `expo-notifications`. | Native dependency and a native rebuild are approved in principle. New question **O8** below (transport when the app is closed). |
| O7 | "Bé đã làm xong" is stored on the device only. | No server field; local storage key per run and activity step; cleared when the run is closed. |

### 15.2 Captions that match the video exactly (new track C)

**Single master clock.** The story timeline in milliseconds, snapped to frame boundaries (scene length = whole frames at the render fps), is the only
clock. Scene clips, narration placement and captions are all derived from it, so none of them can drift independently.

**How cue times are obtained without Whisper.**
1. Each narration or dialogue line is split into clauses at punctuation (comma, full stop, semicolon, dash).
2. VieNeu synthesises each clause as its own audio chunk, so the **real duration of every clause is known** from the audio itself.
3. The assembler places the chunks inside the line's window with fixed short gaps; the cue for a clause starts where its chunk starts and ends where it ends
   (plus a hold of up to 200 ms, never past the window end).
4. If narration is switched off at request time, TTS is skipped and cues use the planned clause windows (proportional to syllable count inside the line window).
5. The caption text is the **display text** exactly as in the confirmed script; numerals and abbreviations are normalised only in the text sent to TTS, and
   the mapping display↔spoken is stored so the evidence can show both.

**Caption formatting for children (lint, fails the build if violated).** ≤ 2 lines, ≤ 32 characters per line, break at word boundaries, reading speed
≤ 14 characters/second for 36–71 months and ≤ 18 for the older bands, minimum on-screen time 1.2 s, no cue crosses a scene cut unless the sentence does,
dialogue cues carry a speaker label (`Rùa:`), no overlap between cues of the same lane.

**Delivery.** The API returns the cue list with the playback source (`captions: [{start_ms,end_ms,text,speaker_ref}]`) and a WebVTT sidecar is stored with the
asset. The app draws captions itself as an overlay driven by the player position (`progressUpdateIntervalMillis` 50 ms), because external subtitle tracks are not
reliable in `expo-av` on Android. Captions are therefore independent of the audio switch and work with sound off.

**Parent options (stored on the device).** `Giọng kể` on/off (instant mute, plus "skip narration" at request time to save GPU time), `Phụ đề` on/off, caption size
small/medium/large. Defaults: narration on, captions on.

**Accuracy tests (acceptance for track C).**
- Unit: cues sorted, non-overlapping per lane, inside `[0, duration]`, text equals the script display text byte for byte (hash), lint rules above.
- Assembler: onset of each placed audio chunk (energy onset by cross-correlation with the chunk) equals the cue start within ±20 ms; total audio length equals video length within one frame.
- Video: scene cuts found by `ffprobe` scene detection equal the timeline boundaries within ±1 frame.
- UI: with the player position log, a caption becomes visible and hidden within ±100 ms of its cue (measured on the emulator; logs kept as evidence).
- Human: the owner watches the three M10 videos with sound on and off and signs off the captions.

### 15.3 Changes to the plan from this amendment

- **Backend work packages:** add `CaptionPlan` (pure domain) and the clause-level TTS chunking in package 5; extend the job projection/playback response with `captions`;
  extend the request body of `video-generations` with `narration: bool` (default true; the contract change is additive).
- **UI (section 11.1):** player gets the caption overlay, a small control row (`Giọng kể`, `Phụ đề`, size); story review shows the caption preview per scene;
  `expo-notifications` setup (permission prompt after the first video request, Vietnamese rationale text, Android channel `video-ready`).
- **UI tests added:**

| ID | Steps | Expected |
|---|---|---|
| U16 | Play the ready video with sound on | captions appear at the cue times; spot-check five cues against the audio by ear and the position log (±100 ms) |
| U17 | Switch `Giọng kể` off while playing, then on | audio mutes and unmutes instantly, captions keep their timing |
| U18 | Switch `Phụ đề` off, change size S/M/L | overlay hides; size changes without overlapping the controls; preference survives app restart |
| U19 | Request a video with narration off | generation finishes sooner (no TTS stage in the stage list); captions still present and aligned to the planned windows |
| U20 | Seek back and forward, pause/resume, rotate device | captions follow the position, no stale cue stays visible |
| U21 | Background the app while generating (permission granted) | a local notification appears when the state becomes READY and opens the video step |
| U22 | Tick activity steps, force-stop, relaunch | ticks restored from device storage for the same run |

- **Milestones:** M6 now includes clause-level TTS, `CaptionPlan` and its accuracy tests; M9 includes the caption overlay, options and notifications; M10 runs U1–U22.

### 15.4 New open question and prerequisite

- **O8 — notification when the app is fully closed.** A local notification only works while the app process is alive. Waking a closed app needs a server push
  (Expo Push, which on Android uses FCM). `AGENTS.md` says Firebase is Authentication-only, so a push transport needs an owner decision and an ADR (and a stored
  push token per parent account, which is personal data). Default until decided: local notification while the app is alive or backgrounded, in-app chip and badge otherwise.
- **P1 — Hugging Face token as a Modal Secret** (section 15.1). Without it the FLUX download job cannot run.
