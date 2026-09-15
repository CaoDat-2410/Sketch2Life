# FEAT-023 decisions

## D-023-01 — Objective ownership belongs to the variant

Family metadata may declare `allowed_objective_ids`, but each variant owns a
`primary_objective_id` and optional `secondary_objective_ids`. The primary
objective is the first objective handed to the existing P1 contract. Objective
coverage is measured from variant-level values.

## D-023-02 — Demo and production eligibility are separate states

Expansion records remain demo-only: `review_status=DEMO_ELIGIBLE` and
`production_eligible=false`. Only an explicit `PRODUCTION_APPROVED` status may
set `production_eligible=true`; the invariant is validated at load time.

## D-023-03 — Butterfly enters by coverage-based replacement

The new `ANIMAL_BUTTERFLY` family replaces one redundant expansion family only
after an offline coverage report identifies a candidate with no unique Tier A/B
concept, objective, age, safety, or prerequisite coverage. The total selectable
catalog remains capped at 300.

## D-023-04 — Debug trace is backend-only

The workflow may emit a sanitized Top-5 ranking trace behind an explicit debug
flag. It contains identity, rank, score dimensions, hard-filter result, reason
codes, and the selected-loss explanation; it never contains prompts, chain of
thought, token dumps, or raw child data.

## D-023-05 — Duration is typed and backward-compatible

Single-session and multi-day duration are represented by a versioned duration
object. Legacy `duration_minutes` is derived for old consumers and is not the
source of truth for multi-day activities.

## D-023-06 — Validation is split by failure domain

The offline 100–300-scene corpus validates deterministic catalog/matcher
behavior. A separate 15–30-scene Lightning smoke validates ASR/VLM/fusion to
selection integration. A release candidate requires both reports.
