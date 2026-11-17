# FEAT-020 Age Variation Decisions

## D-020-11 — Cover all current age bands

**Status:** confirmed
**Date:** 2026-09-12

The demo must cover all four catalog bands: `0-3`, `3-6`, `6-9`, and `9-12`. The single E2E test will execute them as an age matrix rather than choosing one default age.

## D-020-13 — Supported product age is under nine

**Status:** owner-confirmed; supersedes D-020-11 for product execution
**Date:** 2026-10-06

The supported product/GenAI matrix contains `0-3`, `3-6`, and `6-9` only, covering 0–107 completed months. Reject 108+ month profile/session requests before activity selection or provider execution. Preserve the 9–12 catalog band as source data; do not include it in the current product matrix.

## D-020-12 — Never use a fixed first-match result

**Status:** confirmed
**Date:** 2026-09-12

Hard eligibility filters run first. Eligible candidates are then shuffled by a fresh per-run seed, with no-immediate-repeat protection. An explicit seed remains available for deterministic debugging. The image/anchor identity remains stable; age-dependent context and selection are allowed to vary.
