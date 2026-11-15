# Plan Rev87.30 — Publish all pending FEAT-063 worktree changes

**Date:** 2026-11-15<br>
**Status:** APPROVED by the owner's direct instruction to commit and push all feature work.<br>
**Baseline:** current branch `codex/feat063-parent-docker-modal-seed-20261111`, after commit `513d5c96`.

## Objective

Publish all remaining FEAT-063 implementation, configuration, tests, SRS/context records, plans and evidence currently pending in this worktree. The last Rev87.29 test/evidence commit is already pushed and is not duplicated.

## Scope to include

- Parent application, profile/story/activity APIs and contracts, migrations, persistence, Modal client and tests.
- Teacher SVG guide/editor/presentation UI and related tests.
- SVG engine, curated source data/licenses, Modal catalog and worker changes.
- Root Docker Compose, service Dockerfiles, auth-emulator/MinIO setup and placeholder-only `.env.example` changes.
- FEAT-063 SRS §32 and the corresponding plans, approvals, context, decisions, source register, status, ADR and feature-owned evidence.
- Workspace manifests/lockfiles required by the implementation.

## Exclusions and publication hygiene

- Do not publish real `.env` files, provider tokens, Firebase service-account files, seed credentials/accounts or child data.
- Exclude generated pytest temp trees and browser profile caches from Git; keep curated screenshots, reports, SVGs, request summaries and sanitized logs.
- Replace workstation-specific absolute paths in publishable docs/logs/scripts with repository-relative or neutral placeholders. Evidence must preserve result, timing and provenance without exposing local machine paths.
- Keep `.env.example` values as placeholders; do not turn them into actual credentials.

## Commit grouping

1. Backend/domain/API, Parent mobile flow and persistence contracts.
2. SVG catalog/source data, Modal workers and Teacher SVG editor/presentation.
3. Docker/local service configuration and package manifests.
4. FEAT-063 SRS, plans, approvals, context, decisions, status and evidence.

Combine or split these groups only where Git dependency/ownership makes a smaller coherent commit clearer. Use conventional commit messages scoped to FEAT-063.

## Acceptance criteria

- Every remaining implementation file intended for FEAT-063 is committed; generated caches and sensitive local material remain uncommitted/ignored.
- All `.env.example` files contain placeholders only and no credential-bearing files or real child data enter commits.
- Repository security validator passes; `git diff --check` passes for all staged commits.
- Commit list and push result are recorded. Do not claim tests passed unless existing evidence directly supports that claim; this publication task does not rerun product tests.
- Push the commits to the current feature branch's upstream; do not merge to `dev`.

## Authorization

The project owner directly clarified on 2026-11-15: “commit tat ca feature nay len, ko phai moi cai nay”. This authorizes publishing the pending feature changes under the exclusions above.
