# FEAT-071 — PR #27 conflict resolution

- Status: APPROVED / IN_PROGRESS
- Owner: Project owner
- Goal: integrate the current `dev` base into PR #27 with every conflict resolved against the approved feature scopes, then leave PR #27 open and unmerged.
- Scope: conflict resolution and preservation of changes already present on either parent; feature-local plan, approval, decisions, evidence, status, and root approval record.
- Non-goals: merge PR #27 into `dev`, change the PR base, rewrite history, deploy, alter product requirements, add provider/runtime behavior, or perform unrelated cleanup.
- Dependencies: current `dev` `c87d8008b70910eb0a4d3579b9490312e7e3143f`; PR head `f13726bb2325ffd0e7f90e5c7e0221853167cbc0`; common ancestor `1431ef81972b71303fd4a7909748fd3005769a3c`.

## Context snapshot

PR #27 consolidates the web portals into `apps/web`. Its approved FEAT-066/067 records keep Parent Android/mobile outside the web migration. The current source register records FEAT-063 Rev61–65 account, Parent/Teacher flow and presentation work on `dev`. Conflict resolution must preserve those source changes while keeping the one-web-app boundary. The canonical product baseline remains the unsigned FEAT-063 v2.7-draft Rev60 SRS; this task does not change requirements or its approval state.

## Source references

- PR: https://github.com/CaoDat-2410/Sketch2Life/pull/27
- Product authority: `docs/context/SRS_AUTHORITY.md` and the canonical FEAT-063 SRS.
- Current source register: `docs/context/SOURCE_REGISTER.md`.
- Governing feature scopes: FEAT-066 Rev28–30 and FEAT-067 Plan Rev1/Amendment 1 in the PR branch.

## Owner steering update — 2026-11-16

After the Rev1 conflict-resolution commit was published, the owner changed the earlier no-merge instruction and directly authorized merging PR #27 into `dev`, with known CI errors to be handled later. Rev2 covers only a standard GitHub merge attempt; branch protection and required checks must not be bypassed.
