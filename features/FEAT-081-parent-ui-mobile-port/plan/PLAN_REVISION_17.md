# FEAT-081 Plan Revision 17 — Parent UI Alignment to Owner-Supplied SRS Rev67

## Status and authority

This plan records the owner's 2026-11-15 instruction to use the supplied FEAT-063 v2.7-draft Rev67 SRS for a Parent mobile UI review and to fix FE-only mismatches where safe. The supplied document is 634,291 bytes with SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`, matching the Rev67 pin previously recorded by FEAT-081. This task does not modify the repository-wide SRS authority register or the SRS document.

## Goal

Align the visible Parent flow with Rev67 where the current FE can do so without inventing service behavior:

1. Require server-confirmed, current consent before a Parent learning flow can start or resume.
2. Require a confirmed main activity before story generation/rewrite/script confirmation. The current service adapter has no activity selection operation, so show an unavailable state and block progression instead of bypassing the SRS requirement.

## Authorized files

| Kind | Path | Incoming bytes | Incoming SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts` | 7,811 | `D0863F5436E885A022FDF651AE837CB3E7523FAB2F8B0BCBF6B1D640C4D42D9C` |
| E | `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` | 4,825 | `15E8EE976D72D16C33B419C6536C8EFC9525EA3940E39407D80FBB84C7A0EA33` |
| E | `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx` | 7,417 | `6EF4C70D357D205D5B877C75133DE7A6DEBA7EEB23A5F5072ACC7C3968CB9554` |
| E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 18,181 | `E9C62EB5618738E9B43E6ADD72BF2D041A376D3DDFF2608048010810F3DF0650` |
| E | `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx` | 25,549 | `12CADA2A59349A6D2BA53E8F66ECC24797E4BB4D32474198AC1B260EC280CE17` |
| E | `apps/ui-mobile/tests/parentFlowV1.test.ts` | 24,490 | `D64638EADBD7FDEB43B04D56831F9CBF7D8A06B576FB2FE7CC751537371129CF` |
| E | `apps/ui-mobile/tests/parentSrsBehavior.test.ts` | 58,523 | `9A5E00D37AD64A354AAC170933E6AF4D3B908FC1B9AAC590A3D286E4735FCCE3` |
| E | `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md` | 16,314 | `BE3EEF0541B90A0105506C6B6371AB45B9A0C20C4E220B4804345AA633240C82` |
| N | `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_17.md` | — | — |
| N | `features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_SRS_REV67_UI_ALIGNMENT_20261115.md` | — | — |
| E | `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md` | 86,154 | `6E3AC7929D2EC3BA9641488695C3F8AB983158D2C36717F701A72F83C67ED694` |

## Implementation rules

1. Pending, unavailable, revoked, or otherwise unverified consent must not pass the Parent learning gate. Only a server-confirmed consent state with a non-empty policy revision permits the flow.
2. Remove the Activity screen's direct route to Story. Keep exact-pinned lesson activities informational while selection is unavailable; do not invent a selected activity or send an activity payload.
3. Add an explicit `mainActivityConfirmed` presentation prop to StoryScreen. The normal app and offline preview pass `false` until a confirmed selection service exists. Disable generation, same-request retry, rewrite, and script confirmation while false; retain read-only display of an already returned story.
4. Update only existing assertions/test expectations in the two allowlisted test files. Add no test case.
5. Append the owner-authorized approval record and a concise evidence report. Do not edit `CONTEXT.md`, `DECISIONS.md`, the SRS, or the repository-wide authority register.

## Out of scope

- Implementing or calling an activity suggestion/selection API, changing API payloads/contracts, or modifying backend/domain/application services.
- Enabling the no-lesson path; the current app contract and prior FEAT-081 record do not establish the endpoint contract for that route. Report it as still unavailable pending contract confirmation.
- Audio transcription, video admission/playback, post-video activity display, run complete/cancel/delete, history service integration, or any other missing backend capability.
- Tests, typecheck, validators, emulator, install, network, backend, Android build, Modal, staging, commit, or push unless separately requested.

## Acceptance criteria

- Unavailable or pending consent cannot enter Parent learning; the UI reports the existing truthful unavailable state.
- No user-visible action can skip main-activity selection and reach script creation. Story actions remain disabled until the app receives an explicit confirmed-selection state.
- Offline preview call sites provide the new prop and remain inert.
- Existing assertions describe the Rev67 behavior; no new test case is added.
- The evidence report distinguishes corrected FE behavior from requirements still blocked by absent service contracts.

## Relationship to prior decisions

This owner-directed Rev67 correction supersedes only the earlier FEAT-081 consent-unavailable non-blocking behavior and the no-activity bypass into story generation. It does not authorize any missing API/backend behavior. D-016's no-preset/backend-contract limitation remains in force for the current implementation.
