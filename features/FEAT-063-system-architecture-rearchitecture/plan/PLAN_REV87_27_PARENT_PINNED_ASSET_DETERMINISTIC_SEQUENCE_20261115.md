# Plan Rev87.27 — Deterministic sequence for the pinned Parent SVG source

**Date:** 2026-11-15<br>
**Status:** Approved under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”.<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; implementation evidence only in §32.<br>
**Predecessor:** Rev87.26 used its two-request limit. Attempt_002 ran for 172.675 seconds and returned HTTP 502 because Qwen's visual-review assignment had one empty stage. The draft inference and review inference both completed; this was a structural rejection, not a timeout or GPU allocation delay.

## 1. Goal

Return and visually verify one real Parent API result from the exact catalog-backed kitten source, without another nondeterministic stage-assignment/review failure. The source SVG remains authoritative for all 20 guide geometries. The seven-stage sequence is the source-specific, locally rendered and visually inspected mapping already recorded in EV-063-121.

## 2. Bounded change

1. Before Qwen stage-assignment and visual-review inference, check whether the selected catalog candidate matches both `openclipart-friendly-kitten-icon` and raw source hash `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`, with exactly `source_segment_001` through `source_segment_020` and the pinned initial segments 005–006.
2. For this exact match only, build the already reviewed seven-stage plan deterministically from the unchanged catalog segments and continue through existing construction schema, geometry, exact-once, provenance, safety, and adult-review requirements. Qwen remains in the flow for catalog-query expansion/source selection. Do not run draft stage assignment or visual-review inference for this source-specific plan.
3. For every other asset or source revision, leave the current Qwen draft + visual-review flow unchanged.
4. Add regression tests proving the exact-source fast path scope, seven stages, all 20 IDs exactly once, unchanged segment geometry, and the unchanged generic Qwen path.
5. Deploy the Modal dev app, call CPU `/health`, and run at most one real synthetic Parent API request for `con mèo`. No child profile, photograph, voice, consent, video, account or database data. Render and inspect every stage.
6. Stop the Modal app and verify it is stopped. Record logs, timings, output and visual decision in EV-063-121; close Rev87.26 as failed at the hard gate; append as-built evidence to SRS §32 only and update FEAT-063 context/decision/status/evidence index.

## 3. Acceptance criteria

- The exact pinned asset returns the seven-stage construction guide and all 20 unchanged source paths exactly once.
- Stage captions match the newly visible paths; the cumulative result clearly forms the catalog kitten from outline through face details, tail and paws.
- Generic/nonmatching sources still invoke the existing Qwen draft and visual-review path.
- Existing public Parent API schema, draft/adult-review status, source lineage and hard validation remain unchanged.
- Focused worker and backend tests, compilation and local render checks pass before the single route request.
- The single real synthetic route request either returns HTTP 200 with a visually accepted result, or terminates and is documented without retry.
- Modal app is stopped; no child data, personal data, video, database/account/consent/seed/secret/`.env` mutation, Volume mutation, Docker/UI/Teacher edits, SRS §§1–31 changes, commit, push or merge.

## 4. Explicit limits

Maximum one new real route request and one Qwen catalog-query expansion inference. No unchanged retry, second request, video, gate weakening, catalog-volume mutation, production data/publication, credentials, database, Docker/UI/Teacher work, commit/push/merge. Stop after the single result; a further live inference requires another owner instruction and plan.

## 5. Allowed paths

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_svg_topic_stroke_guide_contract.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/run_parent_stage_grounding_rev87_26.py` (allow only `attempt_003` for this plan)
- This plan and `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/**`
- FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`, `evidence/README.md`
- FEAT-063 SRS §32 only and `docs/context/SRS_AUTHORITY.md`

No other paths may be edited.

## Execution closeout — Rev87.27 (2026-11-15)

- **Status:** COMPLETE for the exact pinned Openclipart kitten source; no further inference is authorized by this plan.
- The one authorized synthetic Parent route request returned HTTP 200 in 73.116 seconds with 20 unchanged source paths across seven stages. It remained private, non-persisted and adult-review-required.
- Manual review of the genuine cumulative render found the kitten recognizable by stage 3, with subsequent eye, tail and paw strokes matching Vietnamese step copy. Exact source geometry/path coverage was independently verified. The source illustration is monochrome.
- Checks: Modal worker 49 passed; backend contract/API 12 passed; compilation, focused Ruff, local rendering and exact-geometry validation passed. Full worker-file Ruff still reports 16 findings in the existing broad file. This route harness used a synthetic Parent principal and bypassed the auth guard; it is not Firebase or Android E2E.
- Qwen3.5 catalog-query expansion ran once. For this exact asset/hash only, stage assignment and visual-review inferences were skipped; nonmatching assets retain the prior Qwen path and are not validated by this result.
- Modal `sketch2life-srs23-language-audio-dev` was stopped and verified stopped with zero tasks. No child data, video, Volume mutation, credentials or production request was used. SRS §32.37 and EV-063-121 record the as-built result; target §§1–31 remain unchanged.
