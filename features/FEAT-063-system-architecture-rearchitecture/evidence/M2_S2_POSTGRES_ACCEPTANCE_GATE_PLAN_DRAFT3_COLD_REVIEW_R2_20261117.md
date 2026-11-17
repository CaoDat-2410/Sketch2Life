# FEAT-063 M2 PostgreSQL acceptance gate plan Draft 3 — cold review R2 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2).
- **Pin reviewed:** `plan/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT3_20261117.md`, 24,003 bytes, SHA-256 `85672E6E50E164E08FAADA06C4229B98197320C4D5DF75A3E37316F131C679AC`, at HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a`. The reviewer states the pin matched, that it made no writes and connected to nothing, and that everything is code reading, not a run.
- **Verdict:** NOT READY — P1=1, P2=8, P3=8.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Status of the 17 findings of review R1 (on Draft 1)

Resolved: 3 (by decision PG-D8), 5, 9, 11, 13, 15, 16. Resolved in design with residual gaps: 1 (see N4, N5), 6 (N5, N11), 8 (N13). Partly: 4 and 7 (N2), 10 (N8, N16), 12 (N4), 14, 17 (N8). Resolved on paper but not in substance: 2, the restart (N1, N6).

## New findings

| ID | Sev | Finding | Reviewer's smallest fix |
|---|---|---|---|
| N1 | P1 | The restart leg cannot do what the plan says. "A late result is refused ... through the new process" is unreachable: after a cancel the run is `DELETE_PENDING` and the routes refuse before the provider is reached, with different codes (`PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT`, `PARENT_STORY_RUN_NOT_ACCEPTING_ARTWORK`, or the pending-receipt 409). A late completion can arrive only inside the request that spans the cancel, and a restart destroys that request. And there is no start-up recovery or reconciliation code for Parent story runs, so "recovery không tạo duplicate" has no code path to exercise: the leg proves persistence, replay and a released lock, not recovery. Section 9's claim that a pass shows "the baseline restart leg" overclaims. | Drop that clause; state that the leg proves persistence, replay, released lock and one new create, and that no recovery code exists. Optionally, with an owner decision on expected semantics, kill the process while a provider stand-in call is blocked and check the state left behind. |
| N2 | P2 | Provider seam, control channel and staging are undefined. The router constructs the provider clients inline; without a source edit the only seams are rebinding names in the router module (which the plan's own rule forbids) or injecting a fake `modal` module so that the real client code runs against a fake SDK. A late result needs the stand-in to block mid-request while a second request cancels, across processes, which needs a pause channel the plan does not name. Reaching the script-generating state needs artwork attachment (a valid image, a scanner object, a storage object), subject confirmation, context confirmation and a story payload that passes the draft validators. | Choose the fake-module seam and classify it; define the pause channel; list the staging steps; map the four cases to the Draft 18 rows; or reduce level H and declare it. |
| N3 | P2 | Baseline clauses of M2-AT-08 neither covered nor declared: no cancel of a run that has passed PREPARATION_REVIEW; no assertion that results, assets and receipts are retained after cancel (D-127); no Teacher actor (the route admits only the Parent role); no job or outbox count. | Add a case that cancels from PREPARATION_REVIEW and asserts retention and no new job or outbox row; declare the Teacher clause as not coverable. |
| N4 | P2 | The password rule contradicts how configuration is read: Alembic and the application accept only a URL setting, so a password is either in a URL variable or supplied through a password file with a passwordless URL, which the plan's clearing rule might remove. | Specify the password-file route and exempt it from clearing, or accept a per-process variable scanned out of outputs. |
| N5 | P2 | Clearing the environment does not stop the settings classes from reading a `.env` file one level above the backend root of whichever checkout is imported. | The card pins the import path and prints it in the probe; a pre-run check that no `.env` is present at that root. |
| N6 | P2 | The stop mode (abrupt or graceful) is not chosen and nothing proves the new listener is a different process. | Abrupt termination as primary; record old and new process identifiers; assert the old one is gone and the port refuses connections before restart. |
| N7 | P2 | Seeding and per-case isolation are unstated: an active adult-identity row with the Parent role, issuer and account; a second Parent; a synthetic-origin profile with revisions at 36 and 120 months; the held row of case 08-01a stays active for its account and breaks later cases for that Parent; repeated concurrency tests need fresh accounts. | A seeding table and an account-per-case rule. |
| N8 | P2 | The decision table is not self-contained: four rows cite "chấp nhận 6 đề xuất" and the six proposals are not listed; numbering has gaps. | List them; explain or renumber. |
| N9 | P2 | The "does not show" sentence omits PREPARATION_REVIEW, retention, Teacher, absence of recovery, stop mode, the stand-in and verifier replacement, and the uncovered locale and metadata clauses of M2-AT-10. | Use the deviation list below. |
| N10 | P3 | PG-D8 is legitimate but must be labelled an owner-approved deviation that inverts the baseline sentence: both the profile revisions and the run's stored age enforce 36 to 120; the wider 36-to-155 range lives in a BE1 table the Parent create path does not read, so "legacy rows out of range" has no table on this path. | Label it; consider asserting the run-table check too. |
| N11–N16 | P3 | "Empty" means two different things in two guards, and the socket guard does not cover the launcher process; repetition count, all-must-pass and fresh accounts must be fixed; the fallback Vietnamese message is not in the message dictionary; case 08-01a does not say how the test knows the create is blocked; Docker notes (manifest digest versus image identifier, Alpine collation, no trust authentication, excluded Windows port ranges); housekeeping (an absolute path in the plan, constant names the security validator flags, the launcher's environment list, re-pinning when G2 changes the launcher). | As listed. |

## Deviations the reviewer says need explicit owner decisions in an approval text

1. PG-D8: database refusal replaces the baseline's service-level refusal at 121 and 155 months and inverts "Test không giả định DB chặn 121".
2. Locale and profile metadata of M2-AT-10 are not covered.
3. No cancel from PREPARATION_REVIEW and no retention assertion, unless added.
4. No Teacher actor.
5. The restart leg is persistence only; no recovery path exists to exercise; the stop mode is recorded.
6. A synthetic verifier and a provider stand-in replace real wiring.
7. Direct-SQL seeding of states and identities.
8. Removing a rehearsal container against "no drop by default".
9. Whether a G1-only pass satisfies D-151 C4 and C5 and the proposed S3 condition while M2-AT-09 has no result.

## Reviewer's "checked and found correct" (summary)

The baseline quotes match the source character for character; the ten-head count by reading; no migration needs a superuser, an extension or a role; the blocking and conflict-mapping mechanism of case 08-01a is real; the case expectations for 08-02 to 08-09, 08-14 to 08-16 and the repository-level guards match the code; the identity verifier is replaceable by attribute assignment after application creation; application start-up does no network work under the test environment as far as the constructors were read; a database-level custom setting is a sound run marker readable by a non-superuser; CI runs an explicit file list.

## Checks by the coordinating session after the review

- `routers/parent_ai.py` constructs the three provider clients inline at lines 182, 329 and 486. N2's premise confirmed.
- `parent_story_repository.py` lines 553-554, 906-907 and 936-937 hold the state guards and codes the reviewer cites. N1's unreachability argument confirmed at those points.
- A text search of the application factory, both runtimes, the repository and the service found no start-up recovery or reconciliation hook for Parent story runs; the only lifespan is the StoryRun-lite demo one. Confirmed as a search result, not a proof of absence.
- `settings.py` lines 19 and 122 read a `.env` one level above the backend root. The root checkout has such a file; this worktree does not. N5 confirmed.

## Disposition

Not addressed. Draft 3 is not revised. Three review rounds on this plan have each returned NOT READY. The remaining findings are less about wording than about what the baseline asks for versus what the product has: several baseline clauses name behaviour that does not exist in the code (start-up recovery, a Teacher actor, locale persistence, out-of-range stored ages). The owner must decide those before another draft is useful.
