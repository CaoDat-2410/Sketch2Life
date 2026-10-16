# B2-R01/R02 correction and current handover —2026-10-15

> Historical local-fix/package-build checkpoint. The subsequent user-reported Studio18B2passed/
> 0skip +224PhaseApassed/0skip and final B2 closure are in PHASE_B_B2_CLOSURE_REVIEW_20261015.md.
> Its WAITING_STUDIO/NOT_RUN next steps below are superseded; do not repeat the same B2 run.

- Executor: Codex, explicitly requested by user after Claude usage limit; exact source is
  B2_CODEX_EXECUTOR_HANDOFF_20261015.md. Existing Phase B planrev3 B1–B6 approval remains in force.
- State: **B2_FIXES_LOCAL_PASS / WAITING_STUDIO_POSTGRES**. B2 is not READY_FOR_REVIEW; real
  migration/constraint checks are NOT_RUN. B3 NOT_STARTED; parent BE2-01 IN_PROGRESS/cards14/WIP1.
- Original Claude B2 delivery/review and old package are preserved as historical evidence. This
  record supersedes the old untouched-corrections/old-package next step, not the approved scope.

## Changes and verification

| Group | Concrete correction | Actual local proof | Remaining obligation |
|---|---|---|---|
| B2-R01 | Five opaque-ID columns in job/semantic_request/cancellation_notice use128 consistently in metadata and initial AI migration; actual ErrorCode fields retain80 | Before fix81/120 cases failed at width80; after fix both pass through accepted contract, Phase A fixture create, metadata and frozen migration SQL. Independent read-only code review PASS | Two81/120 PostgreSQL round-trips and the full migration matrix NOT_RUN |
| B2-R02 | Runner validates trusted package/source, captures pytest/tee failures immediately, stops on required setup/provenance failures, permits verified exact-applied retry and rejects unrelated changes |26 mock cases PASS, repeated after final digest repin; bash syntax PASS; independent read-only code review PASS at stated scope | Real Linux/Docker/PostgreSQL run on named Studio NOT_RUN |

The only backend files changed by this correction are tables.py, the initial ai_jobs migration
and B2 test_migrations.py. The shared Alembic environment, BE1 history, contracts/domain, historical
Phase A/Phase B approvals, approved plans, EOF disposition and .gitignore are preserved.
No new repository/UoW/fence/queue/worker adapter is implemented in B2.

| Check | Actual result |
|---|---|
| B2 suite, current source |8 passed,10 skipped; all10 PostgreSQL cases NOT_RUN |
| Six Phase A suites |223 passed,1 known local Pillow skip; earlier user-reported supported-runner live-route PASS is historical, not current B2 migration evidence |
| Ruff, format, mypy with explicit backend config |PASS on five B2 files |
| Runner regressions |26 mock cases PASS; exact script hash matches final package |
| Package |Eight current file hashes match; reverse check PASS; forward apply to isolated pristine-base scratch checkout PASS and all resulting file bytes/hash match |

Runner proof includes each suite failing alone, both failing, both passing; required activation/
provenance/Alembic/log failure; modified source/package; pristine apply, exact rerun and retry
after a mock Docker failure; unexpected tracked/untracked changes rejected without overwriting.
Mock PASS is only control-flow evidence, not server execution. Receipts stay ignored under
evidence/local/b2-codex-fix-20261015/, with runner/results.json and per-case outputs.

## Current package (use this, not the old eb9d package)

Base:993a26cae78c0a4fe983033f03881838c886b176. Directory:
evidence/local/b2-studio-package-20261015/.

| File | sha256 |
|---|---|
| b2_source.patch |f388ce3646db5844ca8baabe17db657e0580a92fc21f800f75753e139a419bff |
| b2_source.sha256 |25e83f2965730083225a9d05f1539edf52f8cd75afb2ed7a6397fb23e47b06f2 |
| run_b2_on_studio.sh |7e26933c7a369eb97c28ef1d7edccd38fab13031485eb815fede9360916baa85 |
| be2-b2-studio-20261015.zip (exact three files above) |8530368f52757c02bd623d65a53d27d8c85677d9f40ecd6960a49f594702974e |

Full eight-file source manifest is in package.json/b2_source.sha256 and current metrics. It
describes base+selected B2 changes, not all dirty local documentation or the pre-existing EOF
test whitespace disposition. No secret/media/user data is included. The ZIP is local-only.

## Next operator step

On **sketch2life-backend-test**, put the three package files in $HOME/be2-b2-package/ (or extract
the ZIP there using the Studio UI), then run:

```bash
cd "$HOME/be2-b2-package"
bash run_b2_on_studio.sh
```

The runner checks branch/base/hash and only applies to pristine source or reuses the exact
already-applied current package. If an older package or other edits are present it rejects them;
inspect the mismatch and preserve those changes, do not reset/clean to bypass the guard.

It retains existing network/runner/private-file secret mechanism and tests only generated
be2_b2_<random> databases. No service/volume recreation or migration of be2_synthetic.

Collect provenance.txt, pytest-b2.txt and pytest-phase-a.txt from the printed timestamped
evidence/local/b2-postgres-20261015/run-<UTC>-<pid>/ directory, plus the shell exit code. If helpful
the operator can run this immediately after the runner to display that exit code:

```bash
printf 'runner_exit=%s\n' "$?"
```

Record user output as USER_REPORTED_REMOTE with this exact snapshot. Do not treat exit0 alone
as acceptance: all current B2 tests including regressions must pass, PostgreSQL0skip, Phase A no
failures and all required steps exit0. Then B2_READY_FOR_REVIEW and final Codex closure before B3.
No commit/push/deploy/provider call/dependency install or actual Studio execution occurred here.

Updated takeover documents: CLAUDE_SESSION_HANDOVER_20261015.md and
plan/CLAUDE_NEW_SESSION_START_20261015.md now start from the prepared PostgreSQL run, not from
the superseded correction prompt. Final check details: metrics/PHASE_B_B2_CODEX_FIX_CHECKS_20261015.json.
