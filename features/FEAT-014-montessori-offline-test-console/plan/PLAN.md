# FEAT-014 Montessori Offline Test Console plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: BLOCKED_BY_APPROVED_PARENT_FIX
- Owner: Person 1
- Prepared at: 2026-08-25
- Branch: `plan/person-1-montessori-offline-console`
- Estimate: 12-16 hours / 3-4 story points

## Goal

Build an offline, activity-explicit console that lets a reviewer list Golden Activity v2 records, enter a synthetic eligibility scenario, see `VALID_CANDIDATE` or `NO_VALID_ACTIVITY` plus complete hard-rule reason codes, and optionally save a sanitized feature-local evidence run.

## Pre-implementation dependency discovered during planning

The FEAT-013 raw-byte baseline hash is checkout-sensitive under the repository's LF policy. FEAT-014 must not hide this failure. Before C1-02 begins, the separately scoped `FEAT-013/plan/PORTABILITY_FIX_PLAN.md` must be approved, implemented, and passing. This is a local integrity-metadata dependency only; it introduces no cross-person runtime dependency.

## Proposed commands

```powershell
# Browse IDs without evaluating or ranking
python tools/montessori_golden_console.py --list

# Scriptable evaluation of one explicitly selected activity
python tools/montessori_golden_console.py evaluate --activity ACT-0004 --age-months 12 --readiness READY_SEARCH_PARTLY_HIDDEN --material GMAT-0004-PRIMARY --supervision DIRECT --policy CAREGIVER_PRESENT

# Guided local prompts
python tools/montessori_golden_console.py interactive

# Replay a committed synthetic scenario and record sanitized evidence
python tools/montessori_golden_console.py replay tests/fixtures/montessori-console/valid-primary.json --record-evidence valid-primary-demo
```

Exact argument spelling may be mechanically refined during implementation, but changing behavior, scope, write policy, exit codes, or architecture requires plan revision 2.

## In scope

- Extract the existing deterministic Golden eligibility evaluator into a small framework-free test-harness module shared by validator and console.
- List Golden v2 IDs, localized titles, age guidance, supervision, readiness IDs, and material option IDs without selecting a recommendation.
- Evaluate exactly one caller-selected activity from arguments, guided prompts, or a versioned synthetic scenario file.
- Preserve every failed hard rule in stable order: active status, lower/upper age, readiness, prerequisite, supervision, policy, material.
- Render concise human-readable output and stable JSON output.
- Use exit code 2 for a valid blocked scenario and exit code 1 for malformed/unsafe input.
- Optionally record a sanitized run under `features/FEAT-014-montessori-offline-test-console/evidence/runs/<validated-run-id>.json`.
- Add fixture-parity, CLI, interactive, evidence-path, overwrite, malformed-input, and no-network tests.
- Add user instructions, example sessions, architecture/security review, and feature-local evidence.

## Out of scope

- Activity retrieval, ranking, scoring, recommendation, personalization, or automatic activity selection.
- Gate B runtime, Android UI, API, backend orchestration, persistence, auth, storage, queue, telemetry, or deployment.
- AI/model calls or Kaggle/Lightning/Runpod adapters.
- Editing Golden Montessori content, weakening hard rules, or changing FEAT-013 owner decisions.
- Real child data, names, media, narration, free-form observations, medical/accessibility diagnoses, or learning outcome evaluation.
- Production runtime or qualified Montessori approval.

## Proposed architecture

```text
tools/montessori_golden/
  eligibility.py       pure deterministic evaluation, no I/O
  catalog.py           local JSON loading and reference validation
  presentation.py      text/JSON formatting only
  evidence.py          sanitized, feature-confined opt-in writer

tools/montessori_golden_console.py
  argparse + guided prompt adapter

tools/validate_montessori_golden.py
  imports the same eligibility function
```

Dependency direction is `console/validator -> harness modules -> versioned local JSON`. The pure evaluator never imports CLI, filesystem, provider, backend, or UI code.

## Input contract

Allowed fields only:

- `activity_ref.id` and `activity_ref.version=2`;
- integer `age_months`;
- sets of `readiness_ids`, `completed_activity_ids`, `available_material_option_ids`, and `policy_flags`;
- `supervision_level` enum;
- `candidate_status` enum.

Unknown fields fail closed. No free-text user field is accepted. Console evidence stores only these fields, deterministic output, tool/catalog versions, UTC timestamp, and run ID.

## Acceptance criteria

- `AC-C1-01`: `--list` exposes all and only the 20 Golden v2 records with review/non-production state and does not return a ranked or recommended choice.
- `AC-C1-02`: every evaluation requires one explicit existing activity ID/version and validates all input fields/enums/references before evaluation; unknown fields fail with exit code 1.
- `AC-C1-03`: console and Golden validator use the same pure eligibility function; all 74 FEAT-013 fixtures retain identical outputs and ordering.
- `AC-C1-04`: primary and substitute valid paths return `VALID_CANDIDATE`/exit 0; blocked scenarios return `NO_VALID_ACTIVITY`/exit 2 with every applicable reason code.
- `AC-C1-05`: guided mode and scriptable replay are behaviorally equivalent for the same input and produce stable JSON suitable for diffing.
- `AC-C1-06`: evidence writing is opt-in, sanitized, confined to this feature, refuses path traversal/absolute paths/overwrite, and never stores machine-local absolute paths.
- `AC-C1-07`: tool runs with network disabled and imports no backend/mobile/provider framework; architecture and security validators pass.
- `AC-C1-08`: output always displays `PROVISIONAL_OWNER_REVIEWED`, `production_eligible=false`, and a non-production/real-child warning.
- `AC-C1-09`: documentation contains at least one valid, one substitute, one blocked-multiple-reason, one malformed-input, and one evidence-recording example.
- `AC-C1-10`: all tests, deterministic replay, deliberate evidence-path failure, repository gates, traceability, and limitations evidence pass before handoff.

## Tasks and estimate

| ID | Task | Output | Estimate |
|---|---|---|---:|
| C1-01 | Freeze console contract and FEAT-013 inputs | command/input/output spec and baseline hashes | 1.5 h |
| C1-02 | Extract shared pure evaluator/catalog loader | harness modules and fixture-parity tests | 3 h |
| C1-03 | Build list/evaluate/replay CLI | deterministic text/JSON interface | 3 h |
| C1-04 | Build guided prompts and safe evidence writer | interactive adapter and confined run records | 2.5 h |
| C1-05 | Add CLI/security/negative tests and examples | fixtures, unit/subprocess tests, example transcripts | 3-4 h |
| C1-06 | Final docs, traceability, repository gates, handoff | evidence packet and status updates | 1-2 h |
| Total | Independent Person 1 test harness | No cross-person runtime dependency | 12-16 h |

## Verification strategy

- Replay all 74 FEAT-013 fixtures through the extracted evaluator before and after refactor.
- Snapshot text and JSON for primary, substitute, and multiple-block scenarios.
- Exercise guided mode through controlled stdin and compare with scriptable evaluation.
- Reject missing/unknown activity, wrong version, unknown readiness/material, malformed age, invalid enum, unknown field, and cross-activity material.
- Deliberately attempt `../`, absolute-path, duplicate-run-ID, and overwrite evidence writes; each must fail non-zero without writing outside the feature.
- Scan imports and repository security; run with network unavailable.
- Re-run FEAT-002 and FEAT-013 validators to prove no baseline/content/review drift.
- Verify the approved FEAT-013 canonical-integrity correction before extracting evaluator behavior.

## Risks and mitigations

- Accidental recommendation scope: require explicit activity ID and forbid automatic selection/ranking.
- Rule drift: one evaluator shared with the Golden validator plus 74-case parity.
- Unsafe evidence path: accept a restricted run ID, derive the full path internally, and refuse overwrite.
- Real-data misuse: closed input schema with no free-text child field and prominent fixture-only warning.
- Tool mistaken for production: label output and docs as review harness; preserve `production_eligible=false`.
- Console coupling to integration: standard library and local versioned artifacts only.
- Checkout-sensitive parent hash: require the separately approved canonical-JSON integrity correction before implementation proceeds.

## Definition of Done

- C1-01 through C1-06 satisfy AC-C1-01 through AC-C1-10.
- FEAT-013 hashes/content decisions remain unchanged.
- All 74 Golden fixtures have evaluator parity.
- Manual examples and negative evidence are feature-local and reproducible.
- Architecture/team/security/harness validators and all tests pass.
- No ranking, integration, provider, or production behavior is introduced.

## Approval rule

Only revision 1 may be implementation-approved. Any automatic activity selection, ranking, new input data category, external service, write location, production claim, or estimate/scope change requires revision 2 and invalidates prior approval.
