# Plan Rev87.7 — Create one real Parent SVG stroke-guide draft

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instruction “tạo svg đi”.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned. Append environment-specific evidence to §32 only; do not change §§1–31.

## 1. Objective

Produce one actual, non-persisted progressive SVG drawing guide for the non-personal topic `gà`, through the authenticated Parent API and the existing Qwen3.5 Modal worker. The already-open Parent StoryRun is incomplete and cannot be resumed, so this amendment authorizes the independent guide endpoint. It accepts only topic and difficulty; no StoryRun, child profile, child image, audio, lesson, or child-related context is sent.

This uses the pinned Arcadia Science `Gallus gallus` SVG as a visual reference and the installed whiteboard-animation skill as stroke-authoring guidance. Qwen must return new line geometry and 4–8 progressive stages. The server sanitizer, exact schema, topic/chicken topology, reference-provenance, and progressive-coverage checks remain unchanged. The result is a private review-required draft and must report `persisted=false`.

## 2. Execution path

1. Recheck the exact current branch/worktree, root `.env` key presence without displaying values, existing Rev79 Postgres/Firebase Auth services, Modal CLI authentication, and the existing `sketch2life-srs23-language-audio-dev` app. Do not alter `.env` or shared services.
2. Start one temporary API container built from this worktree on host port 8001 in the existing Rev79 Docker network. Use the existing synthetic Parent identity from Firebase Auth Emulator; do not create an account/profile/consent or touch the incomplete StoryRun. Set the SVG capability and Modal dev provider only in the temporary container environment.
3. Verify that temporary API `/health` returns HTTP 200 and that the real Parent guide route is present. If API/auth configuration or readiness fails, stop before Modal deployment.
4. Deploy the existing language/audio Modal app at most once using process-local UTF-8 settings only. No model, secret, GPU class, concurrency, volume, or minimum-container changes.
5. Authenticate the existing synthetic Parent against Firebase Auth Emulator without printing or storing the password/ID token. Send exactly one real request to `POST /api/parent/v1/ai/sketch-guides` with `SvgTopicStrokeGuideRequestV1`, topic `gà`, difficulty `beginner`. The request is non-personal and independent of the blocked StoryRun.
6. Accept only HTTP 200 with Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, Arcadia reference provenance, valid sanitized SVG, 8–64 paths, 4–8 stages, all existing quality gates passed, `review_required=true`, and `persisted=false`. Save the exact API response; extract only its returned SVG document and render a preview from that response. Visually inspect the progression and recognizable chicken anatomy.

## 3. Limits and stop rules

- At most one Modal deploy and one authenticated Parent guide inference; hard request cap 1,800 seconds. No retry, second topic, warmup, video, FLUX, or other AI workload.
- No fixture/canned output, profile/consent/run creation or mutation, database write/migration/seed, lesson/catalog write, publication, production account/data, `.env` or secret edit, shared Docker service stop, shared Modal app stop, volume deletion, commit, push, or merge.
- Do not access child media or include child/profile data. Keep the output private, review-required and unpersisted. If the response fails any contract/provenance/quality gate or times out, preserve only the actual error diagnostics and stop.
- Stop/remove only the temporary API container. Leave shared PostgreSQL/Firebase Auth running. Modal functions must scale down naturally; do not stop the shared deployed app.

## 4. Acceptance

- One genuine API → Modal Qwen3.5 inference returns an actual progressive SVG guide with Arcadia provenance and no child data.
- The response passes all existing server gates, has 4–8 coherent stages that progressively form a recognizable chicken from strokes, and remains `DRAFT`, review-required and unpersisted.
- Save the actual JSON, returned SVG, a renderer preview, timings, worker/API logs and exact failure boundary. No result may be fabricated or substituted.

## 5. Exact path manifest

1. This plan file.
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append approval/hash and outcome).
3. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md`.
4. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-4.json`.
5. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-draft.json` (actual response only, if returned).
6. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide.svg` (actual response only, if returned).
7. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-preview.png` (render of actual response only, if returned).
8. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 only).
9. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`.
10. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`.
11. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`.
12. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`.
13. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`.

No other repository path may change under Rev87.7.
