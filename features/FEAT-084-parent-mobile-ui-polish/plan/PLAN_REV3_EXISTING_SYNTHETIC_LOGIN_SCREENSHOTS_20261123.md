# FEAT-084 Plan Rev3 — Existing synthetic account for Parent screenshots

**Date:** 2026-11-23
**Status:** APPROVED by the project owner's direct request to run the UI and capture screens (2026-11-23).
**Parent:** Plan Rev2 — Android UI screenshots addendum.

## Scope amendment

- Permit sign-in to the already provisioned Parent synthetic account using credentials from the ignored root `<LOCAL_ROOT>\.env`. Do not print, screenshot, copy into evidence, or commit credentials.
- After sign-in, navigate only through screens that can be viewed using already existing synthetic records. Do not create or modify accounts, child profiles, consent records, sessions, lesson data, or backend seeds.
- Ordinary authentication and read-only data retrieval made by the real app are allowed solely to reach and render the screens. No AI/Modal inference, video generation, quota/payment operation, API behavior test, preview harness, or fixture.
- Capture each reachable screen with ADB from the real Expo app. If consent/profile state blocks a screen, preserve that gate and report it; do not bypass it.
- Stop the Metro process and emulator started for this task after screenshots are verified.

## Acceptance

1. Only the pre-existing synthetic account and its existing synthetic records are used.
2. Screenshot evidence is raw emulator output; screenshots contain no credentials or real child data.
3. Report captured screens separately from screens blocked by missing state or prohibited inference/write operations.

## Runtime exclusions

No source-code changes, tests, typecheck, database writes/seeding, AI/Modal requests, commit, or push.
