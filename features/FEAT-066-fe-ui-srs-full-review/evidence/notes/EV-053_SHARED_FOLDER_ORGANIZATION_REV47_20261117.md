# FEAT-066 EV-053 — Shared web folder organization (Rev47)

- Date: 2026-11-17.
- Plan: Rev47, current SHA-256 `82AB4F0E97144E8070E228B0ACDA59CB33102CCFF13C5F7927A0746FFF590E22`; owner approval is recorded in `approvals/TASK_APPROVAL.md`.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.

## Changes

- Organized all 17 former shared-root files into `api/`, `auth/`, `components/`, `navigation/` and `styles/`; preserved `assets/sketch2life-brand-art-20261110.jpg` in `assets/`.
- Rewrote 50 direct shared import/style references across 27 source files and updated moved files’ relative imports. Kept `main.tsx` stylesheet order unchanged.
- Preserved the existing Manager navigation groups and API/auth behavior. Existing dirty `WebAppShell.tsx` and `backendApi.tsx` work was retained; `backendRuntimeConfig.ts` moved without committing or staging.

## Verification

- Source scan: no imports/references remain to the old shared-root paths.
- Content comparison: 14 clean tracked moved files match their HEAD versions except approved relative import changes. The existing dirty WebAppShell was retained, including the four Manager nav groups.
- `npm run build`: passed (`tsc -b`; Vite transformed 2053 modules and built successfully).
- `git diff --check`: exit 0. Git emitted existing CRLF-to-LF normalization warnings for dirty worktree files.
- No application test suite, commit, or push.

## Recovery note

The first build after the bulk import edit failed because a PowerShell one-pair mapping altered punctuation in two clean TSX files. Both files were restored from HEAD; only the approved BrandMark asset import path was reapplied. The subsequent build passed, and the content comparison above confirms the moved clean tracked files retain their expected contents.
