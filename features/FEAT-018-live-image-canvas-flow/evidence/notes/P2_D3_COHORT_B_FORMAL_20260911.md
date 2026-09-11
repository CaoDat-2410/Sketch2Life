# FEAT-018 D3 Formal Cohort B - Execution Attempt Record

## Executive verdict

- INCONCLUSIVE.
- No Cohort B execution was performed. This is a blocked-source record, not a completed
  performance/memory evaluation.
- D3/P2-T1 closure is not recommended for Cohort B. Cohort B remains gated exactly as it was
  before this attempt.

## Why execution did not proceed

The task requested a formal Cohort B run (8 owner-approved images, 4 JPEG + 4 PNG, 3 fresh-process
repeats each) against commit `c77230ca1593d5cd31098b5e58f3ff2a13d18a63`, with an explicit
instruction: "If the approved files do not satisfy the recorded format/scope, stop before
execution and report the exact blocker. Do not silently change the plan or hashes."

Before any hashing or execution, the required source documents were read in full, and all of them
independently and consistently state that Cohort B is not source-approved:

- `approvals/TASK_APPROVAL.md` (Approved P2-T1 D3-R2 evaluation addendum, 2026-09-10): "Cohort B
  execution is not yet source-approved: the owner must visually review the actual four JPEG and
  four PNG candidates against the plan's exclusion list before they are hashed or executed. Until
  then, implementation and Cohort A work may proceed, but Cohort B must stop at its source gate."
- `approvals/TASK_APPROVAL.md` (Owner approval and Cohort A closure, 2026-09-11, the most recent
  entry): "Cohort B remains unapproved."
- `CONTEXT.md`: "Cohort B remains unrun and gated on visual review of eight actual non-sensitive
  images."
- `plan/PLAN.md`: "Cohort B remains gated on visual review of the actual eight non-sensitive
  candidates."
- `plan/PERSON_2_AI.md`: "Cohort B remains gated."
- `plan/P2_D3_IMAGE_ADMISSION_EVALUATION_PLAN.md` (decision D3-U1): approval requires owner visual
  review of every Cohort B image, recorded as `owner_reviewed=true` in a local, git-ignored
  manifest, before hashing or execution ever begins.

A filesystem check confirmed there is nothing to execute even if the approval gate were set aside:

- No D3 Cohort B manifest exists. `features/FEAT-018-live-image-canvas-flow/fixtures/image-admission/`
  contains only the Cohort A / D2 fixtures (`manifest-v1.json`, `evaluation-manifest-v1.json`); no
  `*cohort*b*` manifest of any kind is present, tracked or git-ignored.
- No approved 8-image D3 Cohort B set exists with the required 4 JPEG + 4 PNG composition. No such
  set, partial or complete, was located anywhere in the repository.
- A local 16-image fixture pack does exist (`evidence/notes/CHILD_SAFETY_FIXTURE_PACK_20260910.md`,
  sourced from a git-ignored `tmp/feat018-child-safety-eval-20260910/` directory): 16 synthetic PNG
  images, `N01`-`N08` (expected `CHILD_SAFE`) and `S01`-`S08` (expected `CHILD_SENSITIVE`). This is a
  separate synthetic dataset for a distinct, Person-1-owned child-safety classification track. It is
  not a D3 Cohort B candidate set: it is all-PNG rather than 4 JPEG + 4 PNG, it was never visually
  reviewed or hashed against the D3 Cohort B exclusion list, and its own note explicitly records that
  it is "separate from D3/P2-T1 Formal Cohort A and from the D3 Cohort B source gate." No image from
  this pack was read, hashed, converted, or used in any way by this attempt.

Per this repository's own harness rule ("Do not implement work marked DRAFT, PLANNED, or
AWAITING_APPROVAL") and the task's own stop instruction, execution was not attempted. No image was
read, hashed, converted, cropped, or regenerated; no subprocess running the D3 harness was
launched; no provider, Qwen, Whisper, or network call was made.

## Artifact identity

| Item | Value |
|---|---|
| Target commit | c77230ca1593d5cd31098b5e58f3ff2a13d18a63 (confirmed present in repository history; same commit as the closed Cohort A evidence) |
| Cohort B manifest | not present (no file to hash) |
| Cohort B manifest SHA-256 | n/a |
| Approved candidate image count | 0 of an expected 8 (4 JPEG + 4 PNG) |
| Repeats per image (per approved contract) | 3 (never executed) |
| Sample count | 0 |

## Schema and sample integrity

Not applicable. No samples were produced, so there is nothing to validate against a schema. The
sidecar JSON (`metrics/P2_D3_COHORT_B_FORMAL_20260911.json`) reflects this directly:
`"execution_occurred": false`, `"sample_count": 0`, `"samples": []`, `"aggregates": {}`.

## Per-image and aggregate results

| Image | Min ms | Median ms | Max ms | Sample count |
|---|---|---|---|---|
| (none - no approved D3 Cohort B image set exists) | - | - | - | 0 |

No min/median/max/p95 statistic is reported because no image was admitted for measurement. Per the
approved Cohort B contract, p95 would never be reported for this cohort even if samples existed
(3-repeat groups report min/median/max/sample-count only); this constraint is preserved by
omission here, not violated.

## Validation, memory, protocol, privacy, and reproducibility outcomes

| Check | Outcome |
|---|---|
| Commit/manifest/image hash verification | Not performed - no D3 Cohort B manifest and no approved 8-image (4 JPEG + 4 PNG) D3 Cohort B set exists to hash |
| D3 harness fresh-process execution | Not performed |
| Admission latency / native-memory measurement | Not performed |
| Protocol/hash checks on samples | Not applicable - zero samples |
| Privacy check on produced evidence | Passed - the two artifacts created by this attempt (this report and its sidecar JSON) contain no raw image bytes, no absolute filesystem paths, no prompts, no model/provider output, no secrets or credentials, and no personal data. They describe only the blocked state and cite governing documents by repository-relative path. |
| Reproducibility | Not applicable - no run occurred to reproduce |

## Environmental failures

None observed, because no execution was attempted. This is a governance/approval-gate stop, not a
test, infrastructure, or measurement failure. It must not be conflated with the previously
disclosed and unrelated FEAT-003 gitignored-fixture environmental failures recorded against
Cohort A.

## Quality-check commands run

These were run to confirm the repository remains in a valid, unmodified state after this attempt;
none of them relate to Cohort B execution, which did not occur.

| Command | Exit status | Result |
|---|---|---|
| `pytest tests/unit/test_image_admission_evaluation.py tests/unit/test_image_admission.py` (D3 focused tests) | 0 | 119 passed (61 D3 + 58 D2) |
| `python tools/validate_repository_security.py` | 0 | REPOSITORY_SECURITY_VALID |
| `python tools/validate_architecture.py` | 0 | ARCHITECTURE_VALID |
| `python tools/validate_skeleton.py` | 0 | SKELETON_VALID |
| `git diff --check` | 0 | Clean, no output |

JSON parse check: `metrics/P2_D3_COHORT_B_FORMAL_20260911.json` was parsed successfully with the
standard library JSON parser. All numbers in this report (image count 0, sample count 0, expected
image count 8, expected repeats 3) match that JSON exactly, because both describe the same blocked,
zero-sample state.

## Limitations

- This record documents a blocked attempt, not a measurement. It carries no evidentiary value
  about D2's performance or memory behavior on real photographs; that question remains entirely
  open.
- No code, test, fixture, approval, or shared index was modified to produce this record. No
  commit, push, or pull request was made.
- This attempt does not change, weaken, or reinterpret the Cohort B source gate. The next attempt
  still requires a completed owner visual review and a recorded approval addendum before any
  hashing or execution may begin.

## D3/P2-T1 closure recommendation

Not recommended for Cohort B. D3/P2-T1 remains closed for the synthetic Cohort A scope only (per
the 2026-09-11 owner approval already recorded in `approvals/TASK_APPROVAL.md`), and Cohort B
remains open and gated exactly as before this attempt.
