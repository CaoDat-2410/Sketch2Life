# FEAT-094 Plan Rev 2, Amendment A: how phases 3 to 5 are built, and the Parent screens

- **Date:** 2026-11-26
- **Request (owner, in chat):** "làm full đi r hẵng chạy vid, tối ưu cả giao diện nữa": finish the remaining plan before
  running videos, and improve the app screens too.
- **Baseline:** `PLAN_REV2_LEARNING_VIDEO.md`. SRS FEAT-063 v2.7-draft.

## 1. Learning script (phase 4)

| Topic | Design |
|---|---|
| Switch | `SKETCH2LIFE_STORY_LEARNING` (setting `story_learning`), off by default, on in the local Compose stack |
| Age table | its own table for learning videos: 3–5: 5 scenes × 10 s, 18 words, 3 facts; 6–8: 6 × 10, 22, 4; 9–10: 7 × 10, 24, 5. The older table stays for stories without a learning script |
| Input | `story-generation-input.v3` gains an optional `learning` block: numbers, facts (may be empty), fact source, motion hints, setting, allowed interest tags |
| Facts | approved card for the confirmed main subject; else drafted by the model from the pinned lesson notes; else drafted by the model and marked unverified. A second model pass drops doubtful draft facts |
| Scenes | code assigns facts to scenes (name first, parts, use before last, recap last); the model writes one narration, an English action and an English setting per scene |
| Gates | worker retries up to three times on a named gate; the backend checks the same gates again and refuses the story |
| Storage | inside `story_content` (JSONB) under `learning`; **no database migration** |
| Confirmation | the Parent reads the narration that will be spoken, plus "Con sẽ học được" and the unverified label |
| Video | a story with a learning script is projected straight into the video plan: **no second text model call**; narration equals the confirmed text |
| Profile data | only allow-listed interest tags from the context snapshot (ADR-0027, supersedes item 3 of ADR-0024 for these tags) |

## 2. Picture quality (phase 5)

1. The drawing is never mirrored (its facing direction is unknown).
2. The scene's first frame is also a soft end guide (strength 0.7), to hold the camera and keep the subject in frame.
3. Background prompts ask for open flat ground in the lower third.
4. Output vision check: reported only, until its false positives are measured (plan 7.3).

## 3. Parent screens (new in this amendment)

Scope: the Parent screens of the video flow and the defects seen in the app runs.

1. Story review: readable scene-by-scene script, learning points, unverified label.
2. Waiting screen: real stage and scene progress with an honest time estimate.
3. Resume after sign-in no longer asks to choose a profile when the run already belongs to one.
4. A slow first activity request is picked up again instead of creating a second suggestion set.
5. Buttons do not cut their labels.

Not in scope: other roles, a visual rebrand, new image assets (AGENTS.md rule 6 would apply).

## 4. Known limits, decided before implementation

- Part labels (D1) are drawn without arrows if shown at all: recognition returns no part positions.
- Removing paper-coloured gaps inside the cut-out is not done: it would punch holes into white or uncoloured subjects.
- The 40 knowledge cards stay `DRAFT` until the owner approves them with sources, so runs use model drafts.
- Early keyframes (S7) stay out unless the confirmed script makes them cheap to add.

## 5. Acceptance

A1, A2, A7 and A10 of Rev 2 by automated test; the rest on the live runs that follow, with the 30-drawing evaluation
(phase 6) only after the owner agrees to its GPU cost.
