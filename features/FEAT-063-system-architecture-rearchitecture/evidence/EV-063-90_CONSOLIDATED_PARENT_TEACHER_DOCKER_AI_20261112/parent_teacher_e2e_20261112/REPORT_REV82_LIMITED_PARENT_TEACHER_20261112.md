# Rev82 bounded Parent/Teacher AI verification — 2026-11-12

**Status: PARTIAL.** Real synthetic requests reached Parent drawing and activity inference and Teacher lesson-visual generation. The Parent activity response was correctly blocked by a safety/quality gate; story generation was consequently not called. Video was not called.

## Scope and data boundary

- Followed approved Plan Rev82 §22: one FLUX Teacher visual call, then one Parent registration/profile/StoryRun/drawing/confirmation/activity sequence; no retries.
- Parent account was created through the local registration API and Firebase Auth Emulator. The child profile and consent grant are local synthetic test data; this is not legal consent or real-child data. The drawing was generated synthetic input, not a fixture response.
- The existing seeded Teacher account, organization, classroom and reviewed lesson were reused. No duplicate seed entities were created. The existing successful Teacher lesson suggestion and five-slide Sketch Deck outputs were not regenerated.
- The Parent line guide was reused and not regenerated. No video, production Auth or UI screenshot was part of this bounded §22 pass.
- Modal Apps were stopped by the owner after the test. They were not restarted for a retry.

## API results

| Order | API/workload | Result | Time | Notes |
|---:|---|---|---:|---|
| 1 | `POST /api/auth/v1/registrations` | 201 PASS | 0.078 s | Real local registration; no credentials saved |
| 2 | `GET /api/auth/v1/me` | 200 PASS | 0.013 s | Role resolved as Parent |
| 3 | `GET /api/parent/v1/consent-policy` | 200 PASS | 0.013 s | Local synthetic test policy |
| 4 | `POST /api/parent/v1/child-profiles` | 201 PASS | 0.088 s | Synthetic 60-month profile |
| 5 | `POST /api/parent/v1/story-runs` | 201 PASS | 0.060 s | Topic: deer; synthetic context |
| 6 | `POST /api/parent/v1/ai/drawing-understandings` | 200 PASS | 243.509 s | Qwen3.5 returned `con hươu`, confidence 0.90, `topic_match=MATCH`; adult review required |
| 7 | `POST /api/parent/v1/story-runs/{id}/subject-confirmations` | 200 PASS | 0.044 s | Adult confirmation persisted |
| 8 | `POST /api/parent/v1/ai/story-runs/{id}/activity-suggestions` | **502 FAIL** | 346.064 s | `PARENT_ACTIVITY_QUALITY_GATE_REJECTED`, diagnostic `UNSAFE_ACTION_TEXT`; see below |
| 9 | Parent story revision | NOT CALLED | — | Stopped because activity selection failed the approved prerequisite gate |
| — | Video generation | NOT CALLED | — | Explicitly excluded |

Teacher visual API: `POST /api/teacher/v1/organizations/local-rev82-teacher-organization/ai/lesson-visuals` returned **200 PASS** in 412.987 s. It produced a review-required, eight-step 4×2 deer drawing guide using the pinned FLUX.3 Image Klein revision. The image passed the configured mechanical gate. Visual review still matters: the first panel is sparse and some middle panels change little, so this remains a draft rather than a pedagogical approval.

The fresh Parent sequence took 589.863 s from registration through the failed activity response.

The previously completed authenticated Teacher lesson-plan suggestion and five-slide Sketch Deck remain successful evidence at 240.981 s and 90.303 s respectively. The Deck is a draft requiring Teacher review; this §22 pass did not call those workloads again.

## AI and Modal diagnostics

- Teacher visual worker: `fc-01M783YMBKXKA65D9GR4C45ZGQ`; worker duration 95.076 s. Prompt upsampling 48.163 s, FLUX load 6.375 s, image inference 6.731 s, GPU preflight 7.530 s. API elapsed exceeded worker duration by 317.911 s; safe worker phases do not explain that remaining dispatch/queue/transfer time further.
- Parent drawing worker: `fc-01M784EQZKKCC9CC6WA8Q0W9E6`; Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; worker duration 35.362 s. Model load 19.553 s, inference 7.957 s. API elapsed exceeded worker duration by 208.147 s.
- Parent activity worker: `fc-01M784P25FG7873J86HX0MN8QF`; same Qwen3.5-9B revision; worker duration 117.334 s. Model load 19.044 s, constrained decoder setup 3.689 s, inference 93.500 s. Worker terminal status was `worker_succeeded`; output JSON validated and contained three fallback drafts with `decision=NO_MATCH`.
- The backend rejected the generated fallback because one activity contained a positive unsafe-action match. Two other drafts lacked an explicit outdoor setting. This was a business safety/quality-gate rejection, **not** a Modal timeout or malformed JSON. The hard safety and outdoor gates remain unchanged.
- API elapsed exceeded worker duration by 228.730 s for activity generation. This gap is observed, but the safe logs do not prove whether it is entirely GPU queue, cold start, or transfer time.

## Follow-up code change and verification

The activity prompt in `deployment/modal/srs_v23/language_audio_app.py` now says that every fallback activity must name an outdoor place in its own preparation or instruction text and use only safe, adult-prepared materials. It asks the model to replace an unsafe idea with safe observation or light movement. This tightens the worker prompt to the existing business gate; it does not weaken safety validation.

Focused offline tests passed: **30 passed**, covering the Parent worker contract/prompt and activity service gates; targeted Ruff checks also passed. The prompt change was made after the one allowed activity inference and was **not redeployed or verified live**. Plan Rev82 §22 prohibits a retry; the Modal apps have since been stopped by the owner. A live verification needs a new bounded plan approval.

## Evidence files

- `results_rev82_final_20261112/teacher/teacher_lesson_visual_candidate.png` — actual generated Teacher visual candidate.
- `results_rev82_final_20261112/teacher/lesson_visuals_metadata.json` and `lesson_visual_postfix_summary.json` — model, panel layout, request status and output hash.
- `results_rev82_final_20261112/parent/run_summary.json` — synthetic Parent call sequence and timings; no email, password or token.
- `results_rev82_final_20261112/parent/06_drawing_understanding.json` and `07_subject_confirmation.json` — actual API outputs.
- `results_rev82_final_20261112/parent/08_activity_worker_output_synthetic.json` — complete synthetic worker JSON for the rejected activity result, retained for review.
- `results_rev82_final_20261112/parent/08_activity_suggestions.json` — API rejection envelope.
- `results_rev82_final_20261112/parent/parent_modal_worker_diagnostics.json` — allowlisted phases, model pins, hashes, durations and gate reason; no raw Modal logs or prompts.
- `results_rev82_postfix_20261112/teacher/lesson_plan_suggestion.json` and `sketch_deck_response.json` — prior real Teacher AI outputs.
