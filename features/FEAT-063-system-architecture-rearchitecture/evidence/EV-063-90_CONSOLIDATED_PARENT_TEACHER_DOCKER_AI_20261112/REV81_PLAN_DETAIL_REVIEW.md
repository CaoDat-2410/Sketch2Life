# EV-063-90 — Rev81 consolidated plan detail review

**Date:** 2026-11-12 (Asia/Saigon)

**Result:** Planning artifact expanded; source implementation remains paused.

## Authority and scope

- Product source read: FEAT-063 SRS v2.7-draft Rev60, unsigned, §§1–31, routed by `docs/context/SRS_AUTHORITY.md`.
- Source register read: `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`.
- Plan updated: `plan/PLAN_REV81_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112.md`.
- Plan SHA-256: `9292502F57E7038CFDE6CA7885077FFACE10B6B391F2DB5A8BA022410EE993AA`.
- Approval scope remains planning/documentation only, per `approvals/TASK_APPROVAL.md` and the owner's request to pause coding.

## What the detailed plan now contains

- Parent mobile screens for Firebase sign-in/providers, home/profile CRUD and consent, optional topic/lesson selection, guide, mandatory drawing capture, Qwen understanding, mismatch/one-retake resolution, activity selection, script review, video/playback/activity list, account/settings, notifications, quota, sharing and recent history.
- Teacher screens for structured lesson authoring, filtered upload review, editable presentation slides/media, progressive guide review, occurrence setup, system-selected child confirmation, capture of that child's drawing, understanding and script confirmation; plus School Manager and Platform Admin controls for their separate review scopes.
- Clean-architecture responsibilities for Expo and web clients.
- Current router paths verified from source, clearly separated from proposed contract gaps; request/response, auth, revision, idempotency, error and audit fields required before any API change.
- Logical data ownership, exact-version pins, additive migration sequence, state/business-rule gates, per-workload Modal schemas and quality gates.
- Docker/seed/environment health rules, stable synthetic seed matrix, dependency-ordered work packages, exit gates and a screen/API/AI/security verification matrix. Eleven decisions/open gates remain explicitly listed in Plan Rev81 §9.
- Rev60 conflicts that require a traced Rev61 proposal before implementation. The canonical SRS and Data Table Register were not edited.

## Review and execution limits

- `git diff --check` produced no whitespace errors for tracked changes. The plan and headings were inspected after expansion.
- No source code, migration, SRS, Data Table Register, `.env`, Docker runtime, Modal app or API was changed or exercised by this documentation update.
- No tests, builds, paid inference, deployment, publication, commit or push were run.
- Open choices in Plan Rev81 §9 remain open; no recommendation was silently recorded as an owner decision.
