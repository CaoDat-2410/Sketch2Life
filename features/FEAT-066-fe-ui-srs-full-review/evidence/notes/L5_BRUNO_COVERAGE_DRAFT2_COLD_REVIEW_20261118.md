# FEAT-066 L5 Bruno coverage plan Draft 2 — cold review (round 2) — 2026-11-18

- **Reviewer:** Claude subagent with a fresh context, model Sonnet 5.5, told high effort. It worked read-only by instruction, as part of closing Phase A (owner: "việc 2 bạn làm lun").
- **Pin reviewed:** `plan/PLAN_L5_BRUNO_COVERAGE_DRAFT2_20261118.md`, 14,900 bytes, SHA-256 `1BE8D3EC6D807F68320DA79769FF9A13236F634337EBD74F4977DC97D658EDE9`. These pins also matched: the SRS, register Draft 4, seed Draft 6 and P4.
- **What the reviewer did not do (its statement):**
  - It did not run Bruno or any test, build, validator, app, database, Docker or network call.
  - It did not open the gate secret directory, any `.url` or `.env` file, `environments/*.bru` or `firebase-auth-helper/*`.
  - It used `git check-ignore`, `git diff --numstat` (counts only) and recursive greps that exclude the helper folder.
  - It read the Bruno CLI 4.3.0 source and docs read-only.
  - One Bash call that would also have listed the helper folder was denied by the classifier and did not run.
  - It wrote nothing.
- **Verdict:** NOT READY — **P1=0, P2=2, P3=9**. P2 fell from 7 to 2, and no round-1 finding class repeats. Both P2 items are small text fixes. This is round 2 of 5.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-1 findings (reviewer)

| ID | Status | Note |
|---|---|---|
| B1-01 | resolved | S-2 is done (`.git/info/exclude:153`); `bruno/.env` is covered by `.gitignore:2` |
| B1-02 | partly | CLI mechanics: see B2-01 |
| B1-03 | resolved | 144 request files plus the helper; 86 use `bearerToken` |
| B1-04 | resolved | — |
| B1-05 | resolved | — |
| B1-06 | partly | guard gap: see B2-02 |
| B1-07 | resolved in design | — |
| B1-08 | resolved | — |
| B1-09 | resolved | — |
| B1-10 | partly | overlap and total: see B2-07 |
| B1-11 | resolved | — |

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| B2-01 | §1 rules 3–4, §11 | **Secret persistence and reports in Bruno CLI 4.3.0.**<br>Writes that persist:<br>• `bru.setEnvVar` is persisted to the active environment file, which is the tracked `local.bru`.<br>• Collection-variable writes go to `collection.bru`.<br>Writes that stay in memory: `bru.setVar`, and `--env-var` overrides.<br>Masking in reports: only `.env` values and `--env-var` secrets. Shell `process.env` values and runtime variables are not masked.<br>`--reporter-skip-all-headers` removes headers only. Request and response bodies, such as a sign-in response, stay in the report unless `--reporter-skip-body` is also set. | Scripts use `bru.setVar` only. Every run uses `--reporter-skip-all-headers --reporter-skip-body`. Secrets come from `.env` or `--env-var`, which are masked. |
| B2-02 | §3 rules 3 and 5, §7 L5-0 | **The loopback guard has gaps.**<br>• It checks `baseUrl` only. The Firebase helper calls an external host, outside `baseUrl`, and a collection-root recursive run would reach it.<br>• A loopback `baseUrl` does not prove that the app uses the `seed` database.<br>• `collection.bru` does not exist yet and is not named in the plan. | Guard on the resolved request URL host (a pre-request throw stops the send). Name `collection.bru` as a new L5-0 file. Runs are always folder-scoped to `requests/l5/...`. The owner confirms before each run that the app uses the `seed` database. |

## P3 findings (summary)

| ID | Finding |
|---|---|
| B2-03 | §0 is stale: S-2 is done, and the `local.bru` diff is now 5 insertions and 0 deletions. |
| B2-04 | The CLI reads `.env` from `<collection root>/.env`, not from the repository root. That path is git-ignored. |
| B2-05 | CLI 4.3.0 has `--tags` and `--exclude-tags`, which match both request tags and folder tags. Tag the target folders and run baseline with `--exclude-tags target`. Drop "NV". |
| B2-06 | Map each role variable to `{{process.env.X}}` / `bru.getProcessEnv`. Add O-BRU-AUTH and S-3 to the L5-0 gate. Emulator ID tokens expire, so long runs need re-minting. |
| B2-07 | B03, B04 and C02 appear in two scope rows. Remove the overlap and add a total. |
| B2-08 | The L5-2 baseline cases run on M2 routes that already exist, yet they are gated on FE items (FEBASE, O-MOB2). Gate them on M2 plus seed S1, or justify the FE gate. |
| B2-09 | The "two header values" key case probably cannot be sent from Bruno: mark it NV or move it to a BE unit test. A cascade rule is needed for chained create-change-delete failures and for `seq` ordering. |

## Checks (reviewer)

- **Counts and queues** (7, 8, 11, 6) match register §5.
- **Codes and statuses** agree with D-066-68, D-066-69 and the SRS, including the privacy case.
- **Seed links** to orgs C and G line up.
- **`.env`** is git-ignored.
- **CLI features** were checked in the CLI 4.3.0 source: `--env-var`, `--reporter-skip-*`, the pre-request throw, `skipRequest` and `stopExecution` all exist as claimed.

## Not verified (reviewer)

- The roadmap L5 card (not located).
- Real BE status codes.
- Whether the BE accepts emulator tokens.
- UUID generation inside the safe sandbox.
- The helper's URL (the file was not opened).

## Disposition by the coordinating session

Draft 2 is not edited. A Draft 3 that fixes B2-01 to B2-09 follows, as part of closing Phase A.
