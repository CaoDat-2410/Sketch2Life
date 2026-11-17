# FEAT-023 — Catalog contract hardening and recommendation explainability

Status: IMPLEMENTED_WITH_LIGHTNING_SMOKE_PENDING

## 1. Objective

Correct the remaining catalog-contract defects revealed by FEAT-022 runtime
evidence. The result must preserve the 100-profile rollback path, keep the
MVP cap at 300 selectable profiles, make pedagogy age-specific, add butterfly
coverage, explain ranking decisions safely, and model multi-day activities
without conflating session time with activity span.

## 2. Phase A — Freeze evidence and replacement decision

1. Capture the current FEAT-022 revision, its manifest hash, profile IDs, and
   current concept/objective/age coverage.
2. Run the deterministic evaluator on 100–300 fixed scene cases before editing
   content. Record candidate counts, top activity/family shares, objective
   alignment, NO_MATCH/UNAVAILABLE reasons, and selected IDs by seed.
3. Identify redundant expansion families using evidence, not intuition. A
   replacement candidate must not be the only provider of a Tier A/B concept,
   objective-age pair, material path, safety path, or supported age band.
4. Record the selected replacement and rollback revision in an ADR before data
   migration.

Gate: the replacement is reproducible and the old catalog remains loadable.

## 3. Phase B — Version the catalog schema without silent migration

1. Introduce the next curated catalog schema/revision rather than changing the
   meaning of existing revision `catalog-2026-09-expansion-1` in place.
2. Rename family-level `objective_ids` to `allowed_objective_ids`.
3. Add to each variant:
   - `primary_objective_id`;
   - `secondary_objective_ids`;
   - an explicit age adaptation rationale/observation signal where the current
     contract can carry it.
4. Validate primary objective membership in the family allowed set and reject
   duplicate primary/secondary IDs.
5. Migrate `ACT-0123`, `ACT-0124`, and `ACT-0129` to the approved mappings:
   - `ACT-0123` → `OBJ_SCIENTIFIC_OBSERVATION`;
   - `ACT-0124` → `OBJ_SCIENTIFIC_INQUIRY`;
   - `ACT-0129` → `OBJ_SENSORIAL_DISCRIMINATION`.
6. Preserve practical-life value only as a secondary objective when the
   action genuinely supports it.
7. Update template loading, semantic profiles, objective reports, catalog diff,
   and provenance hashes to use variant-level objective identity.

Gate: no family-level objective is silently treated as the primary objective
for every age variant.

## 4. Phase C — Add pedagogical alignment as a governed signal

1. Add a versioned `pedagogical_alignment` record to the curated variant or a
   companion review manifest. It must identify the primary objective, expected
   observable behavior, and reviewer status.
2. Validate objective/action/challenge/observation consistency with deterministic
   rules and reviewed mappings; AI may suggest, but cannot approve or mutate.
3. Add `objective_activity_alignment` to the sanitized score breakdown. It must
   be derived from the reviewed catalog mapping, not hard-coded to 1.0 because
   the selected objective came from the selected template.
4. Keep the existing hard Gate B behavior: an objective mismatch rejects the
   candidate rather than being hidden by a high semantic score.

Gate: ACT-0123/0124/0129 produce meaningful objective alignment evidence and
bad mappings fail the catalog lint.

## 5. Phase D — Replace one redundant family with butterfly coverage

1. Add a four-variant `ANIMAL_BUTTERFLY` family covering all four age bands.
2. Author distinct age behavior, not translations:
   - 0–3: look, point, and track a large safe butterfly image;
   - 3–6: match butterfly body/wing features or habitat cards;
   - 6–9: compare wing symmetry, life-cycle evidence, or movement;
   - 9–12: design an observation log or explain adaptation/evidence limits.
3. Keep Vietnamese child-facing text, safe materials, direct/nearby supervision,
   and ideal-plus-home-substitute material paths.
4. Remove the evidence-selected redundant family and update all hashes,
   coverage metrics, and rollback/diff reports.
5. Add `ANIMAL_BUTTERFLY` to Tier A only if the corpus confirms it is a common
   scene concept; otherwise keep it as an explicit monitored concept with a
   documented rationale.

Gate: butterfly has at least three safe candidates per age band after filters,
or the evidence explicitly records why fewer are applicable.

## 6. Phase E — Add backend-only Top-5 ranking trace

1. Introduce a typed debug evidence object with:
   `rank`, activity/family/variant/version/revision identity, selected concept,
   semantic score, child-interest alignment, objective alignment, age fit,
   safety, catalog quality, diversity/recency penalty, final score, filter
   status, reason codes, and `lost_to_selected_because`.
2. Emit at most five candidates after hard safety/age/material/prerequisite
   filtering, plus explicit rejected candidates only when their reason is safe
   to expose.
3. Guard the field behind a runtime debug/evidence flag. Public/mobile result
   contracts omit it by default.
4. Ensure stable deterministic ordering for the same seed and stable identity
   parity across semantic match, template, handoff, and trace.
5. Add redaction tests proving prompts, raw provider output, tokens, and child
   media never enter the trace.

Gate: a reviewer can explain why the selected candidate beat the next four
without exposing private model reasoning.

## 7. Phase F — Add typed duration semantics

1. Add a versioned duration model:
   - `SINGLE_SESSION`: `min_minutes`, `max_minutes`;
   - `MULTI_DAY`: `initial_session_minutes`, `daily_observation_minutes`,
     `min_days`, `max_days`.
2. Validate ranges and require `min_days <= max_days` for multi-day records.
3. Migrate ACT-0123 to `MULTI_DAY` with reviewed values; keep its daily action
   distinct from setup and cleanup.
4. Derive legacy `duration_minutes` only for old consumers, using the initial
   session duration, and mark the derived nature in evidence.
5. Ensure Activity Bridge receives the span and daily observation fields.

Gate: no multi-day activity is represented as a single 20-minute event only.

## 8. Phase G — Governance and approved-only runtime

1. Define allowed transition states:
   `DEMO_ELIGIBLE → OWNER_REVIEWED → PRODUCTION_APPROVED`, with
   `DEPRECATED` and `BLOCKED` terminal controls.
2. Enforce:
   - DEMO_ELIGIBLE/OWNER_REVIEWED ⇒ `production_eligible=false`;
   - PRODUCTION_APPROVED ⇒ `production_eligible=true`;
   - unknown combinations fail closed.
3. Keep demo mode explicitly opt-in and keep production loaders closed to the
   expansion until production approval exists.
4. Add migration, rollback, and identity-parity tests.

Gate: status and eligibility cannot drift again.

## 9. Phase H — Verification and release evidence

### Deterministic offline suite

- 100–300 fixed scenes, multiple age bands, ambiguous/multi-object cases;
- concept and objective coverage after hard filters;
- objective↔activity consistency;
- exact/alias/concept/fallback rates;
- family/activity concentration and immediate repeats;
- same-seed reproducibility and different-seed diversity;
- butterfly coverage and explicit unavailable reason codes;
- top-K trace schema/redaction;
- duration and governance invariants.

### Lightning real-AI smoke

- 15–30 representative synthetic image/WAV cases;
- local Qwen VLM and faster-whisper model provenance;
- ASR → VLM → fusion → semantic normalization → catalog selection;
- output manifest and model/catalog hashes;
- no fixture recommendation injection;
- failure classified as model/runtime vs catalog/matcher regression.

### Required gates

- full backend tests;
- Ruff and strict mypy;
- harness validation;
- repository security validation;
- offline corpus report;
- Lightning smoke report for release candidate.

## 10. Acceptance criteria

- Variant-level objective identity is present and validated.
- ACT-0123, ACT-0124, and ACT-0129 use the approved primary objectives.
- Butterfly coverage exists without exceeding 300 selectable profiles.
- All expansion records are demo-only until production approval.
- Top-5 trace is typed, deterministic, redacted, and backend-debug-only.
- Multi-day activities expose initial session, daily observation, and day span.
- Existing baseline rollback remains byte/identity compatible.
- Offline corpus meets the agreed coverage/diversity thresholds.
- Lightning smoke is recorded for release candidate, or explicitly marked
  blocked with exact environment evidence.
