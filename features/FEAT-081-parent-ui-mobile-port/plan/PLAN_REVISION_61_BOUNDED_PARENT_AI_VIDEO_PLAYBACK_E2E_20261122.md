# Plan Revision 61 — bounded Parent AI flow and video playback check

**Feature:** FEAT-081 Parent UI mobile port  
**Date:** 2026-11-22  
**Status:** APPROVED by the owner's direct instruction to check the UI with AI enabled  
**Authority:** FEAT-063 v2.7-draft SRS; synthetic/dev-only validation.

## Goal

Verify that the updated Parent video screen can play the existing or newly completed synthetic preview on Android, and determine which AI/API step prevents reaching it if the current run cannot resume.

## Bounded execution

1. Read-only inspect the existing synthetic Parent run and video candidate first. Reuse a ready candidate if it belongs to the authenticated test profile.
2. Continue through the real Android UI. For each required AI workload, send at most one request only if its result is missing. Do not repeat an ambiguous/failed request. Maximum: one activity suggestion, one story generation, and one video-candidate request; do not regenerate a drawing guide or re-run image understanding if existing confirmed context can be reused.
3. If no resumable profile/run exists, stop and report rather than creating an account or mutating seed data. Reuse the configured local synthetic Parent/profile; do not use real child data.
4. Do not bypass consent, age, ownership, safety, output-quality, or production gates. Do not change quota/payment configuration. If an existing local synthetic technical-preview gate blocks the action, report it; do not broaden a gate.
5. On Android, verify the new Play action advances the elapsed time, Pause stops it, and Play resumes. If playback errors, record the safe UI error and relevant sanitized logs; do not retry the same video-generation job.
6. After the check, stop only Modal apps started/deployed for this task after confirming no active tasks. Preserve any unrelated app state.

## Allowed changes

- No additional product-code changes are pre-authorized by this plan. If a code defect is found, record the minimal repair proposal and approval amendment before editing.
- Feature-local approval, status, context, plan, and evidence records.

## Acceptance and evidence

- Record run/candidate state, AI workload calls and outcomes, response timings, API/worker error codes, and Android playback elapsed-time behavior without saving credentials or raw model output.
- Save Android screenshots for the ready/player state and playback state, plus a concise report under this revision's feature-local evidence folder.
- Report clearly whether playback was confirmed, whether any AI request failed, Modal cleanup status, and any remaining blocker.
- No commit or push.

## Exclusions

No real-child data, new account, seed-data rewrite, quota/payment operation or bypass, new consent text/version, safety/quality-gate bypass, production release, direct DB mutation, repeat inference, or code change outside a separately approved amendment.
