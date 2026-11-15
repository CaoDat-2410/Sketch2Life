# Plan Rev87.20 — Parent construction-stroke live diagnosis and fix

**Date:** 2026-11-15<br>
**Authorization gate:** Implement only after this exact bounded scope and its SHA-256 are recorded in `approvals/TASK_APPROVAL.md`.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; target requirements remain unchanged.<br>
**Predecessor:** Rev87.19; its single inference allowance was consumed by a terminal geometry-validation failure.

## 1. Request and current state

The owner asks to continue testing and fixing the Parent SVG drawing guide. Rev87.19 introduced a separate construction-guide contract, but its only live Qwen3.5 inference completed model generation and was rejected at `output_parse_and_source_identity_validation` with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`. The old combined gate did not record whether the cause was excessive aggregate geometry or duplicate strokes. A local cap/prompt/diagnostic correction was subsequently deployed to Modal `dev`, then the app was stopped, but that corrected worker has not been exercised by a model request.

This plan authorizes a new, separately bounded verification cycle. It does not reuse the Rev87.19 allowance or claim that its failed result was a success.

## 2. Goal

Make the Parent guide produce a valid, understandable progressive construction drawing from a real source-conditioned model response, or establish a precise remaining failure and stop safely. The guide must build the selected animal/object from simple marks toward recognizable parts, rather than merely reveal the source illustration's contours or look like a child's freehand drawing.

## 3. Scope

1. Inspect the current local worker/parser, its deployed `dev` revision, the recorded Rev87.19 failure, and existing local test results. Do not edit unrelated Parent, Teacher, Docker, account, database, or AI workloads.
2. Run the focused worker, backend contract/domain, and Parent mobile checks before any new inference. Preserve existing hard SVG/safety/schema gates.
3. If the current `dev` worker does not contain the local diagnostic correction, deploy only the existing language/audio Modal app to `dev`. Do not upload or mutate the catalog Volume. CPU health/status checks are permitted.
4. Send one fresh real inference using only the generic synthetic topic `con mèo`. No child profile, photograph, voice, consent, account identity, or real personal data is included.
5. If that result fails or is structurally/pedagogically unacceptable, use its safe diagnostics and rendered artifact to make one narrowly scoped code/prompt/parser correction, add a regression test, rerun local focused checks, and make at most one final real synthetic inference. If the first result passes the contract and visual criteria, do not make the second call.
6. Render every cumulative stage from a successful real response and retain the original color source separately. Review the first stage, progression, final subject/pose, stroke/instruction alignment, and child-readable Vietnamese. Save only genuine output and its renders under the evidence folder.
7. After the last permitted inference, stop the Modal app and verify the `dev` app is stopped. Record every API/worker error, stage timing, call ID, model revision, test result, and final app state.
8. Update the evidence, plan outcome, FEAT-063 context/decision/status, evidence index, authority pointer, and SRS §32 only. Do not modify target SRS §§1–31.

## 4. Inference and cost boundary

- Maximum: **two** real GPU inference calls total in this plan.
- The first call diagnoses the corrected deployed worker. The second is allowed only after an evidence-based code/prompt correction and passing local checks; if the first passes all acceptance criteria, stop after one.
- No automatic retry, repeated polling that dispatches work, gate bypass, lowering of hard limits, or synthetic response substituted for model output.
- If the second call fails or still produces an unacceptable guide, preserve the evidence and stop. Any further model iteration requires another owner instruction and a new bounded plan.
- Generic topic only; no child data, video, production requests, or production deployment.

## 5. Acceptance criteria

- [ ] Focused local worker/backend/mobile checks pass before deployment/inference and after any fix.
- [ ] A real Modal response passes worker, API, source/provenance, SVG safety, and stage contracts without weakening a hard gate.
- [ ] The guide has 4–8 sequential stages; the first stage contains only simple construction marks and does not reveal the finished subject outline.
- [ ] Stages progressively add connected large forms, major parts, and a small number of identifying details; no duplicated geometry or unexplained detached marks remain.
- [ ] Each short Vietnamese instruction describes the marks visible in that stage; the final drawing preserves the selected reference's orientation and recognizable defining features.
- [ ] Every cumulative stage and the separate original color reference are rendered from the real response and saved for review.
- [ ] At most two inference calls occurred; the Modal `dev` app is stopped at closeout.
- [ ] Reports state any remaining limitations honestly. No fixture, fake result, or unaudited product output is presented as model evidence.

## 6. Allowed paths

Code and tests, only when needed for this task:

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- `backend/src/sketch2life/domain/svg_engine.py`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/tests/unit/test_svg_construction_guide.py`
- `backend/tests/contract/test_parent_svg_construction_guide_api.py`
- `backend/tests/contract/test_parent_svg_source_derived_guide.py`
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
- `apps/ui-mobile/tests/svgGuideSourceContract.test.mjs`

Task records and evidence:

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_20_PARENT_STROKE_LIVE_FIX_20261115.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/**`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 only)
- `docs/context/SRS_AUTHORITY.md`

Do not modify other paths without a new plan amendment.

### Execution outcome — 2026-11-15

**Status: PARTIAL; acceptance not achieved.** Focused Modal/backend/mobile checks passed (27/27, 12/12, 3/3). The first real synthetic request exposed a missing final feature stroke; the prompt and safe diagnostics were corrected. One final real request then failed the unchanged hard geometry gate: Qwen emitted two duplicate strokes for eight stages (70 geometry characters), producing `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID` / `DUPLICATE_STROKE_GEOMETRY`, HTTP 502 after 189.152 seconds. This was not a timeout. No usable SVG or visual render exists. The maximum two inference attempts were consumed; no further inference was run under this plan. Modal `dev` deployment v2 passed CPU `/health` without GPU/inference on the health request and was stopped/verified stopped after testing. See `evidence/EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/REPORT.md`; SRS §32.34 records as-built evidence only.

## 7. Explicit exclusions

No child/profile/image/voice/consent or production data; no video; no Teacher presentation; no account/database/migration/seed/`.env`/secret changes; no dataset upload or Volume deletion; no SRS target edits in §§1–31; no Docker/UI workflow expansion; no public release; no commit, push, merge, or unrelated cleanup.

## 8. Closeout

Record this plan's approved SHA-256 before implementation. Keep Rev87.19's terminal failure and artifacts immutable. Mark the work complete only if the live result and visual criteria pass; otherwise mark it partial and list the exact remaining failure. Append as-built evidence to SRS §32 without implying product/SRS sign-off.
