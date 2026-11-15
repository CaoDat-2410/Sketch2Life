# Plan Rev87.5 — One bounded retry of curated SVG Parent inference

**Feature:** FEAT-063 — system architecture rearchitecture<br>
**Date:** 2026-11-13<br>
**Status:** APPROVED by the owner's direct instruction “chạy lại đi” after Rev87.4's one deploy attempt failed before updating the Modal app.<br>
**Requirements:** FEAT-063 SRS v2.7-draft Rev69, unsigned; retain Rev87.4 requirements and update only SRS §32 as-built evidence.

## 1. Purpose and prior gate

Rev87.4 implemented the curated Arcadia `Gallus gallus` SVG reference and stroke-authoring rules. Its single deployment attempt failed locally before app update because Windows `Path` formatting generated an invalid Modal remote path. That defect has been fixed in the approved worker source. The owner has now authorized exactly one new bounded run. This amendment does not erase or rewrite the failed attempt and does not authorize repeated retries.

## 2. Authorized run

1. Read the existing project-root `.env` only through process/Compose configuration; do not print, copy, edit, or commit its values. If it is absent or required Modal/Firebase values are missing, stop and report names of missing variables only.
2. Preflight Modal CLI authentication, existing dev app, current-worktree Parent route, existing synthetic Parent access/consent, and UI startup capability without inference. Reuse the already-running `rev79-parent-local-20261112` PostgreSQL and Firebase Auth services and their existing volumes; do not start, stop, initialize, reset or remove those shared services/volumes. Build and run the current-worktree API as a temporary `docker compose run --no-deps --rm` container in that existing Compose network on host port 8001, using the project-root `.env` and enabling the Parent SVG flag only for that process. Do not run `migrate`, seed commands, or create an account. If the existing database schema, Firebase synthetic account/consent, route, or UI is unavailable, stop before GPU inference.
3. Deploy `deployment/modal/srs_v23/language_audio_app.py` once to the existing `dev` app, with the corrected POSIX remote paths. Do not deploy other apps or change secrets.
4. Call only the deployed CPU `health_api` once. It must report healthy and ready without requesting a GPU or loading model weights.
5. Start the real Parent Expo UI using the existing project-root `.env` (no edit), target the temporary API at `127.0.0.1:8001` or the emulator host equivalent, and use only the pre-existing synthetic Parent login. Through the real UI and authenticated backend, send at most one non-personal `gà` sketch-guide request to the existing Qwen3.5 Modal workload. Use the Arcadia reference only for this matching topic. The result must be a real provider response, pass existing schema/sanitizer/anatomy/progression gates, remain an unpersisted adult-review draft, and be rendered for visual inspection. No fixture or canned response may count.

## 3. Limits and stop rules

- One additional Modal app deployment; one CPU health call; at most one authenticated Parent UI GPU inference; 1,800-second hard cap. No warmup, retry, second topic, second inference, video, FLUX, test suite, real-child data, production identity, database migration, seed/account creation, lesson/catalog persistence/publication, secret or `.env` edits, Modal app stop, commit, push, or merge.
- If source/hash/license preflight fails, Modal auth/app is unavailable, local API/UI/synthetic consent cannot be used, deployment fails, health fails, API/UI gate fails, call times out/has unknown outcome, or quality gate fails: preserve diagnostics, restore the local feature flag to false, stop immediately, and do not retry.
- Do not stop shared Docker services or any pre-existing Modal app/container. Stop only the temporary API/UI processes started by this run. Preserve all persistent volumes.
- No product requirement changes. Rev87.4 source and stroke-authoring implementation remain as-is unless a blocker exposes a specific defect; any additional source edit requires a further amendment.

## 4. Acceptance and evidence

A pass requires a successful deployment, healthy CPU endpoint, one real UI→API→Modal response, strict backend acceptance, and a visually recognizable chicken revealed progressively in 4–8 meaningful stages. A deployment/health pass without the UI inference is recorded as partial, not end-to-end success. Save actual response, sanitized SVG, progressive render screenshots, timings, phase logs, and final gate result in EV-063-101. Never synthesize missing evidence.

## 5. Exact cumulative file manifest

Runtime source remains limited to Rev87 §6 plus the Rev87.4 §6 additions; no additional source files may change. This amendment permits only these new/updated records:

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_5_CURATED_SVG_MODAL_RETRY_20261113.md` (new)
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (append approval/hash)
3. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md` (update with second attempt)
4. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-2.json` (actual diagnostics only)
5. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide-draft.json` (actual response only, on success)
6. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/generated-guide.svg` (actual serialized response only, on success)
7. Actual progressive-render screenshots in the same EV-063-101 folder, on success
8. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 evidence only)
9. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
10. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
11. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
12. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
13. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`

The Rev87.4 single-attempt gate is superseded only by this one additional run. No other Rev87.4 boundary changes. The exact running service project was selected during read-only preflight; this clarification avoids recreating the stopped default-project PostgreSQL service after its configured host port was found already allocated.
