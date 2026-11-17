# BE2-07 Claude cloud re-review and bounded remediation — 2026-10-20

- Reviewed starting HEAD: `1d731c53ac48305d07c69c5cbf810ab80cca6559` (equal to origin; clean
  fast-forward from `f0359c4f`). Task base: `23acf9e83e181305edfeb345be9a8e7eb9dbef88`.
- Authority: `../../approvals/CLOUD_REREVIEW_REMEDIATION_APPROVAL_20261020.md` and
  `../../plan/CLOUD_REREVIEW_REMEDIATION_PLAN_20261020.md`, within revision 1 / OD01–08 and the
  approved P3 cloud follow-up.
- Fix commit: `b3f75737f541ac01f8ca3de83f378893ec74baba`. All checks below ran on that tree.
- Verdict: **NO_BLOCKING_FINDINGS after remediation**. One new P3 was found and fixed in scope.
  Nothing is left open in the reviewed scope. This review and the fix were done in the same
  session, so this is not an independent post-fix review. Codex performs the independent
  post-push review.
- Component NOT_ACCEPTED; card IN_PROGRESS / NOT_DONE. Owner acceptance and runtime adoption
  remain separate.

## Findings and dispositions

| ID | Severity | Disposition |
|---|---|---|
| P3-R1 default-ignorable used as a word separator | P3, in scope | **FIXED** in `b3f7573` |
| P3-N1 invisible characters / DEL-C1 | was P3 | **FIX_CONFIRMED** for in-word insertion and controls |
| P3-N2 verifier under -O/-OO | was P3 | **FIX_CONFIRMED** |
| Earlier P2-1..3, P3-1..6 | — | Dispositions unchanged. The six historical service mutants are still killed on the current tree |
| Equivalent-mutant observation | none | No change made |

**P3-R1 — default-ignorable characters used as word separators**

- **Location:** `backend/src/sketch2life/domain/knowledge_bundle.py` (`_literal_signatures` and
  `imagined_literal_overlap`) at `1d731c5`.
- **Trigger:** the imagined literal is `"Mèo có cánh."` and the claim is
  `"Mèoㅤcóㅤcánh."` (Hangul filler instead of a space). The same happens with
  U+115F, U+FFA0, U+17B4 and U+200B. A Hangul filler normally renders as a blank gap.
- **Expected:** `409 IMAGINED_AS_FACT` and a DTO rejection, as for the in-word variants.
- **Observed at `1d731c5`:** the domain overlap was False. The strict record DTO accepted the
  record. The real edit handler returned 200 `generation_ready`, and `resolve_exact` exported
  the imagined sentence as a fact.
- **Cause:** removing the character joined the words into one token, for example
  `mèocócánh`.
- **Fix:** compare every pairing of the "removed" and "word separator" variants of each
  signature. Removal still happens before NFKC, so CGJ between a Vietnamese base and its
  accent still composes. Stored text, projections, canonical bytes and control validation do
  not change.
- **Red evidence:** the new regressions ran on the unfixed source and produced 19 assertion
  failures, 36 passes and 0 errors. The new cases are:
  - domain, both directions, for U+115F/1160/3164/FFA0/200B/034F;
  - token-boundary controls;
  - the strict DTO full-basis record;
  - real edit handlers for the claim side and the trusted imagined side, with a check that
    the full store and commit count do not change.
- **Green evidence:** the same selection had 55 passes after the fix.

**P3-N1 — invisible characters and DEL/C1:**

- Probes through the domain helper, the strict DTO and the real handler reject in-word CGJ,
  variation selectors (including VS17), Mongolian selectors, Hangul fillers, tag characters
  and ZWSP.
- CGJ between a base and a Vietnamese accent, NFD text, reverse containment and an
  obfuscated trusted imagined side are also rejected.
- Domain and DTO both reject C0, CR, DEL and C1 (including NEL). LF and TAB are accepted.
- Stored text is unchanged.
- The Unicode 15.0 range table matches DerivedCoreProperties `Default_Ignorable_Code_Point`.

**P3-N2 — verifier under -O/-OO.** Run on a temporary detached checkout of `f0359c4f` with the
current verifier and provenance overlaid:

| Case | Normal Python | -O | -OO |
|---|---|---|---|
| Valid historical pins | exit 0, `PORTABLE_EVIDENCE_VALID` | exit 2, no success token | exit 2, no success token |
| Wrong commit | exit 1 | exit 2 | exit 2 |
| Tampered README byte | exit 1 | exit 2 | exit 2 |

- `PYTHONOPTIMIZE=1` also exits 2.
- At the current HEAD, normal mode exits 1 with "reviewed current file changed". This is the
  documented behaviour: the historical product pins reject the corrected N1 bytes. It is not
  a regression.

**Earlier dispositions:**

- On a copy of the final tree, the six historical service mutants (M01, M04, M06, M07, M09,
  M10) are each killed by assertions: 360 cases, 0 errors.
- The new mutants S01–S05, S07 and S08 are also killed. They drop the separator variant on one
  side or both, drop the default-ignorable ranges, or weaken control validation.

**Observation (no change):** mutant S06 removes the default-ignorable filter that runs before
NFKC. It survives the suite and also survives an exhaustive probe, because the filter and NFKC
that run after casefold already recompose the accent. The code comment overstates how
necessary that first filter is. Behaviour is unchanged.

## Verification on the final tree

- **Six task07 modules:** 360 passed, 0 failed/errors/skips. That is 338 before the fix plus
  22 new cases.
- **Exhaustive probe:** covers all 4,206 points in the Unicode 15.0 default-ignorable set plus
  runtime Cf. Each point is placed inside a word, between a base and an accent, as every
  separator, and as one separator, in both directions, with token-boundary and unrelated-text
  negative controls. Result: 50,472 comparisons, 0 failures.
- **Ruff check and format:** pass on the 16 task07 files and the verifier.
- **Strict mypy:** pass on the 10 task07 source files.
- **Validators:** harness, architecture, skeleton and repository security all exit 0.
- **`git diff --check`:** 0 for the worktree. Base..HEAD reports only the documented frozen
  `TASK_APPROVAL.md` EOF exception.
- **Whitespace audit of changed and new files:** OK.

## NOT_RUN / limits

- **Approved 56-module batch: NOT_RUN.** The selection exists (50 baseline plus 6 task07
  modules in `OFFLINE_BATCH_PROFILE_POST_CLOUD_P3.json`). This cloud environment lacks
  fastapi, sqlalchemy, structlog, boto3, redis, rq, alembic, psycopg, firebase_admin,
  pydantic_settings and httpx, and installs are forbidden. The earlier local
  1,663/1,660/3-skip batch remains historical, not re-verified here, and does not cover this
  fix.
- **Pillow-dependent live-app checks** and the excluded V2 server module: NOT_RUN.
- **Runtime, provider, DB, HTTP and Lightning:** NOT_RUN.
- **External or foreign-checkout invariants:** NOT_VERIFIABLE_ON_CLOUD.
- **Tool versions:** pytest 9.1.1 and mypy 2.3.1 are outside the pyproject dev ranges. Python
  is 3.13.16 with unicodedata 15.1.0. pytest came from an existing uv tool venv on
  `PYTHONPATH`; nothing was installed.
- **Historical records not rewritten:** the POST_CLOUD_P3 map, checks and handoff are left as
  they were. They do not include the 22 new cases.
- **Raw outputs:** the raw outputs of this run are in ignored
  `../local/claude-cloud-rereview-20261020T072237Z/`. They are listed in that run's
  `OUTPUT_INDEX.json` and delivered as a separate archive.
- **`evidence/cloud-review/`:** unchanged. Its cleanup remains held.
