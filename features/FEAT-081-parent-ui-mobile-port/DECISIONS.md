# FEAT-081 — Owner decisions

Owner: Person 2 (AnhKhoaa157).
Recorded: 2026-11-12.

| ID | Decision | Basis |
|---|---|---|
| D-001 | Target apps/ui-mobile, the Expo SDK 52 / React Native 0.76.9 / React 18.3.1 Parent app on dev. The web sample UI in sibling worktree .worktrees/ui, branch feature/fe-ui-full-remediation at commit 30c94342, mainly apps/parent-ui, is read-only reference material. | direct owner instruction 2026-11-12 |
| D-002 | CaoDat built the existing ui-mobile base. The owner will edit the Parent UI from here on; no per-file ownership reservation is required. Merge risk remains because CaoDat may later edit the same files on dev and must be stated in the plan. | direct owner instruction 2026-11-12 |
| D-003 | Use feature ID FEAT-081 and folder features/FEAT-081-parent-ui-mobile-port. A read-only check found no FEAT-081 folder on origin/dev, feature/fe-ui-full-remediation, or origin/codex/fe-ui-web-remediation, and no local or remote-tracking branch name containing FEAT-081. | direct owner instruction 2026-11-12 |
| D-004 | Use existing Vitest 3.2.4 through the package script test: vitest run tests && node scripts/validate-ui-copy.mjs. Do not add Jest or change package.json or pnpm-lock.yaml in this feature. | direct owner instruction 2026-11-12 |
| D-005 | Wave 1 is P01/P02 (home and lesson gallery) using the alternative allowlist in PORT_ORDER_AND_ALLOWLIST_DRAFT_R2.md. Do not edit shared components/ui.tsx. | direct owner instruction 2026-11-12 |
| D-006 | For the later, separately approved move to apps/mobile (plain React Native 0.87 / React 19.2), new screens use only React Native View, Text, Pressable, StyleSheet, and Animated primitives. Media picking, audio recording, and browser opening go through application ports, with Expo-only code in infrastructure adapters. Icons use react-native-svg components, not @expo/vector-icons. Add no Expo gradient or other Expo-only library in new screens and no new Expo-only dependency. Follow AGENTS.md dependency direction: interfaces/adapters -> application -> domain; infrastructure implements ports. | direct owner instruction 2026-11-12 |
| D-007 | Waves 2-5 are outline only and need separate approvals. Hold P08c, P14, and P15 until a product requirement is recorded. Do not copy any sample image, avatar, icon, or font until it is generated under assets/generated with provenance and visual approval, then passes the repository asset gate before application. | direct owner instruction 2026-11-12 |
| D-008 | Out of scope: the Android applicationId / validate_skeleton CI fix, the move to apps/mobile, and wiring the client to new backend routes. Those routes exist only on a private, unpushed integration branch. Wave 1 uses synthetic fixtures only and makes no API change. | direct owner instruction 2026-11-12 |

These decisions authorize this feature's recorded Wave 1 approval only. Implementation has not launched; later waves and the apps/mobile migration remain separate gates.
## D-009 — FEAT-081 implementation location

- Decision: Keep apps/ui-mobile as the implementation location for FEAT-081 Wave 1 and for any separately approved FEAT-081 Parent UI follow-on wave. Do not move or duplicate those FEAT-081 screens into apps/mobile.
- Scope and reconciliation: This is a feature-scoped implementation-location exception. It does not amend the canonical FEAT-063 v2.7-draft Rev60 SRS, change its broader apps/mobile Parent product target, or globally supersede ADR-0020 or ADR-0021. The older D-006/D-008 future-move wording is superseded only for FEAT-081 and its separately approved follow-on UI waves. Any product-wide or production-target change requires a separate owner decision and SRS/ADR revision.
- Reference: ADR-0023-feat081-mobile-ui-target.md.
- Basis: direct owner instruction 2026-11-12.
- Exact DECISIONS.md SHA-256 immediately before appending D-009: 35CC570FABE7144ECB8B9B3AE098E484A4E432D7FEDE5448FD6FACFCC3997CB9.
## D-010 - FEAT-081 Wave 2 API wiring plan approval (not launch)

- Decision: Approve Wave 2 API wiring for FEAT-081 under `plan/PLAN_REVISION_3.md`, an exact copy of the owner-pinned R2 draft. Wave 2 is APPROVED / NOT LAUNCHED. The plan's `DRAFT` header is superseded by Addendum 4; no implementation is launched by this decision.
- Owner product decisions:
  1. Tomorrow's StoryRun requires a lesson preset/version pin.
  2. `drawing-understandings` stays unchanged and receives no added `Idempotency-Key`.
  3. Consent and data-authorization calls stay removed; no consent-return path is designed here.
  4. `activity-suggestions` is not mounted; use the existing Activity screen skip action.
  5. Use synthetic profiles; restore existing profiles through the profile list route.
  6. `OWNER_MODAL_CALL_APPROVED=NO`; the owner-run flow stops before `drawing-understandings`.
- Launch gates: 2A and 2B are separate. 2A requires a separate explicit owner launch instruction. 2B requires its own instruction after 2A passes.
- S1a-P2 basis: The pending, not-yet-ACCEPTED list/delete/Parent-role-gate contract is accepted as the working basis for 2A and may change slightly. Any change after S1a-P2 acceptance is handled by a new addendum.
- Wave 2 baseline: Owner-run results at 2026-11-12 23:56 and 2026-11-13 00:15 on bytes identical to commit `3c75b10d` are the baselines: `pnpm run test` reported 4 files / 29 tests passed and `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics; `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` all exited 0. These results consume the baseline invocation of each command in the approved ceilings.
- Command ceilings: `pnpm run test` 3 total; `pnpm run typecheck` 3 total; each of `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` 2 total. The baseline invocation is consumed.
- Pinned plan: `plan/PLAN_REVISION_3.md`, 34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.
- Previous DECISIONS prefix pin: 3,950 bytes, SHA-256 `3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805`.
- Post-append DECISIONS.md byte length and SHA-256 are recorded in Addendum 4, status/context, and the command ledger after this append.
- Basis: direct owner approval dated 2026-11-13.