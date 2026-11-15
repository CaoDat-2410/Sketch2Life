# Plan Rev86 — Teacher SVG dataset pack correction and one real comparison

**Feature:** FEAT-063 system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner in this conversation after the Rev85 terminal validation failure.<br>
**Requirements source:** FEAT-063 v2.7-draft SRS Rev69, unsigned. This is a worker/data correction; change only SRS §32 as-built evidence. Do not change §§1–31.

## 1. Problem statement

Rev85 deployed a dataset-conditioned Teacher SVG worker and used its only approved real UI inference. The API returned terminal HTTP 502 before Qwen inference because whole-pack validation found cat example path path-026 with stroke_width 20, beyond the existing strict 1–12 contract. The Qwen result and visual comparison were therefore not produced. Evidence is in EV-063-95.

The fix is to exclude the invalid cat exemplar from the active reference pack, keep the byte-preserved raw source snapshot, record the exclusion and recompute every dependent hash. Preserve the existing parser, output schema, local feature flag, and model. Do not normalize or relax the offending stroke width.

## 2. Objective

Make the packaged dataset pass the exact worker parser for every included record before deployment, then perform one real authenticated Teacher UI generation for the same non-personal deer topic used in Rev84/Rev85. Compare the actual rendered output with EV-063-94 using the existing five qualitative checks. A single result is a bounded sample, not a general quality benchmark.

## 3. Scope and acceptance criteria

### Dataset correction

1. Preserve source-examples.jsonl byte-for-byte and preserve the pinned dataset revision d7ab3149308746a4b17e7cbee30f1f054f6c49df.
2. Remove prompet-sample-cat from the active reference-pack-v1.json. Keep dog/quadruped and rabbit/lagomorph only; the existing topic selector may return no exemplar for feline topics.
3. Move the cat record into dataset-manifest.json not_selected_from_preview_subset with its original source row/SVG hashes and a precise exclusion reason: path-026 stroke_width=20 exceeds the existing parser maximum 12. Do not alter source geometry/style or claim it passed validation.
4. Recompute the active pack byte count and SHA-256, update the worker's pinned pack hash and workload metadata, and correct README curation statements.
5. Before deployment, run one bounded offline preflight using the exact worker parser against every packaged example, and verify JSON parse, pack byte count/hash and manifest agreement. Require all included examples to pass. This is a static validation, not a test-suite run. If it fails, stop before deployment and inference.

### One real runtime comparison

1. Reuse the existing local synthetic Teacher account, local API/Auth Emulator and real authenticated Teacher UI path. No fixture, mock output, or prior response reuse.
2. Update only the already-deployed Modal app sketch2life-srs23-language-audio-dev once, if needed. Do not deploy another app.
3. Call its CPU /health once. Continue only if the pinned Qwen3.5-9B revision is ready and health is good; no GPU warmup.
4. Trigger exactly one UI inference for topic con hươu sao, age 60 months and style warm_storybook. No retry or alternate input. Preserve the 1,800-second hard cap.
5. Save the actual JSON, SVG and rendered PNG only if returned by the real flow. Record request ID, timings, worker phases, dataset reference ID/hash, API response and Modal result. Do not fabricate output on failure.
6. Compare with EV-063-94 across: recognizable deer anatomy; coherent body/head proportions; connected and grounded limbs; markings/details attached to the subject; and absence of detached/unrelated objects. Record each criterion and limitations. Do not claim the single sample proves general quality.
7. On inference failure, timeout, unknown outcome, schema/sanitizer rejection, or visibly unclear output, preserve evidence and stop. Do not retry or relax parser/schema/quality gates.

### Cleanup and records

- Restore the local SVG capability flag to false without editing .env.
- Close only the task-started Teacher UI/browser process; preserve the user's existing Docker services and data.
- Keep the shared Modal app deployed; require min_containers=0 and allow configured scale-down. Do not stop shared Apps or other containers.
- Update workload status, FEAT-063 context/decision/source/status/evidence index, and append an environment-specific SRS §32 note only. The SRS remains unsigned.
- No commit, push, merge, database migration/seed, video, FLUX, additional dataset download, production Auth, child data, secret output, or unrelated source change.

## 4. Bounded resource limits

- No new public dataset fetch; use only the already-pinned local source snapshot.
- Maximum one update to the existing language/audio Modal App, one CPU /health call, and one real authenticated UI-triggered GPU inference.
- No warmup, retries, second topic, other AI workload, extra Modal app, or minimum live containers.
- One request only; the model request may incur GPU startup billing even if it fails. Exact charges are read from Modal billing, not inferred from worker logs.
- If the post-run container query does not return, record scale-to-zero as unverified; do not stop the shared app to force it.

## 5. Exact file manifest

Only these files may be changed for Rev86; preserve all pre-existing worktree changes:

1. features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV86_TEACHER_SVG_DATASET_PACK_FIX_20261113.md
2. features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md
3. deployment/modal/srs_v23/language_audio_app.py
4. deployment/modal/srs_v23/workloads.json
5. deployment/modal/srs_v23/data/teacher_svg_illustration/README.md
6. deployment/modal/srs_v23/data/teacher_svg_illustration/dataset-manifest.json
7. deployment/modal/srs_v23/data/teacher_svg_illustration/reference-pack-v1.json
8. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/REPORT.md
9. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/generated-svg-draft.json (create only from actual response)
10. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/generated-svg-draft.svg (create only from actual response)
11. features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/teacher-svg-draft.png (create only from actual browser render)
12. features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md (append dated §32 as-built evidence only)
13. features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md
14. features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md
15. features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md
16. features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md
17. features/FEAT-063-system-architecture-rearchitecture/evidence/README.md

If any additional path is needed, stop before editing it and request a new approval. Do not modify source-examples.jsonl.

## 6. Sequence

1. Record the exact approved plan hash in TASK_APPROVAL.md.
2. Correct the active pack/manifest/README, update worker hash pin and workload status.
3. Run the bounded static preflight against the exact worker parser; stop on any discrepancy.
4. Verify the current local API/UI and Modal deployment state read-only; start only the Teacher UI if needed. Do not reset Docker data or migrate/seed.
5. If necessary, deploy the existing Modal app once, then call CPU /health once.
6. Make exactly one authenticated UI request and capture actual result/diagnostics. No retry.
7. Restore local capability false; close task-local UI/browser; leave shared app deployed and allow it to scale down.
8. Complete evidence and §32/context/status updates. Report the real outcome and unresolved limitations.

## 7. Known limitations

The pack is a tiny structural prompt reference set based on synthetic/model-generated public examples without paired prompts. It may nudge broad composition but does not establish accurate deer anatomy. Excluding the cat leaves no feline reference. Two remaining examples do not constitute representative coverage of all illustration topics. Educator review and a broader owner-approved evaluation remain necessary before enabling this workload beyond local testing.
