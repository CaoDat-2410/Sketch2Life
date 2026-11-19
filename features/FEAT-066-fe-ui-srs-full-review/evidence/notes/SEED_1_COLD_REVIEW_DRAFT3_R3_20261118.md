# SEED-1 Draft 3 — cold review record (round 3, 2026-11-18)

- **Artifact:** `plan/PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261118.md`, 20,100 B, SHA-256 `FE732B49560198142F4D303DBE00397B2FB8951F537A2529A0F8248195BB7E74`.
- **Reviewer:** a fresh subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and statically.
- **Pin check:** PASS. It covered Draft 3, the seed design Draft 6 (`CABC4BCA…`), the round-2 record (`4A19BFAD…`) and HEAD `08439b22` with a clean `backend/`.
- **Verdict:** **READY WITH NOTES**. P1 = 0, P2 = 0, P3 = 7.

**P1 + P2 by round:**

| Round | P1 + P2 |
|---:|---:|
| 1 | 4 |
| 2 | 2 |
| 3 | 0 |

- Neither repeat class (lesson visibility, StoryRun columns) recurs at P1 or P2.
- **Round-2 status:**
  - S2R-01 and S2R-02 are fixed. The reviewer walked the visibility rule against `service.py:1280–1309` and every `story.runs` and `run_inputs` constraint, including the migration-only `ck_story_run_actor_refs`. `get_run` needs nothing else for any of the five states.
  - S2R-03, S2R-05, S2R-06 and S2R-08 are fixed.
  - S2R-04 and S2R-07 are mostly fixed; the residue is S3R-05 and S3R-03.

## Findings (all P3)

| ID | Finding (short) | Fix (Draft 4) |
|---|---|---|
| S3R-01 | Two line cites are wrong: `_sha256_json` is at `:1643–1644`, and the JSON-null comment is at `:135–136` | Correct both |
| S3R-02 | The lesson content shape is under-specified. The content must also validate against `LessonContentInputV1`. `content_json` is stored without `activities`; the hash covers the full content; `activity_order` starts at 1 | State all four |
| S3R-03 | The `parent.command_receipts` and `story.command_receipts` exclusions are design departures, but they are not called that | Mark them as departures for the decision row |
| S3R-04 | The import list is incomplete: `VerifiedPrincipal`, the storage, parser and scanner port types, `get_settings` and `get_core_database_settings` | Add them |
| S3R-05 | `git add -N` has no path, and a broad add would catch unrelated FEAT-066 notes | Explicit paths for the nine task files; note the intent-to-add index entries |
| S3R-06 | Seeded runs are readable but static. A `PREPARATION_REVIEW` run cannot advance, and the `FAILED` run has no `error_code` or `job_state` | Say they are display-only; set `error_code` and `job_state` on `FAILED`; state that `typed_idea` equals a non-empty `adult_confirmed_idea`; validate records through `ParentStoryRunResponseV1` in test 7 |
| S3R-07 | The seeded issuer is fixed in `data.py`, so SD-5 sign-in must use the same issuer | Add one line to SD-5 |

## Outcome

The package is ready for owner approval after the seven P3 fixes. The coordinator writes Draft 4 with those fixes only; whether to re-review it is the owner's decision. The SEED-1 code still waits for its BE queue slot (after CONV-1 and FR-C-08).
