# FEAT-066 L2 Billing contract Draft 6 — cold review (owner-granted extra round) — 2026-11-18

- **Reviewer:** a Claude subagent in a fresh context, model Sonnet 5.5. The caller set effort to high; the reviewer reported it cannot see that setting. It was read-only by instruction.
- **Round:** round 6. D-171 item 11 allows five rounds; the owner granted one extra round on 2026-11-18 ("Draft 6, review thêm").
- **Scratch folder:** `tmp/feat066-billing-review-d6/`, created and left empty.
- **Pin reviewed:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT6_20261118.md`, 44,622 bytes, SHA-256 `E8E2BFFC8052BD05713B5FE48E7F8789477C1CBD1757495E5B974DBE7572488B`.
  - Also matched their pins: Draft 5 (`9BB4B395…`), the round-5 record (`9B043776…`) and the adopted SRS in the root checkout (`B9B1F42D…`).
  - The Draft 5 → Draft 6 diff matches the header; there are no unannounced changes.
- **What the reviewer did not do (its statement):**
  - It changed no file outside the scratch folder.
  - It ran no test, build, validator, linter, type checker, app, Alembic, database, Docker, network, provider or Modal command, and no state-changing git command.
  - It opened neither the gate secret directory nor any URL, `.env` or secret file.
  - It used only `sha256sum`, `sed`, `grep`, `wc` and `git diff --no-index`.
- **Verdict:** NOT READY (narrowly) — **P1=0, P2=1, P3=7**.
  - P1+P2 did not fall (1 → 1).
  - The create-against-downgrade class appears for a fourth time, in a narrower sub-path (in-flight timeout).
  - The reviewer notes that F6-01 can be fixed in text only, or accepted as a residual.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 finding

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F6-01 | §7.3 step 4 (timeout); §4 rule 7a; §4 step 5 | A BE1 call timeout does not prove that Billing has finished. Billing may still be blocked on its subscription lock or committing.<br><br>The failing interleaving:<ol><li>Create C waits on the BE1 lock, holding answer v0.</li><li>Downgrade D times out and commits null.</li><li>C takes the lock and re-reads Billing, which still answers v0.</li><li>C sets the stamp to v0 (rule 7a) and inserts.</li><li>Billing then commits v1.</li></ol>Only the later event repairs the stamp. Rule 7a holds only for schedules already committed, and §4 step 5f does not list this case. | State that Billing's `lock_timeout` and `statement_timeout` for `schedule_downgrade` are strictly below BE1's call timeout. State that the Billing session is closed before null is written. List "Billing commit completing after BE1 gave up" in 5f and §12. |

## P3 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F6-02 | §4 step 5f; §7.3 step 6; §12 | The 5f bound is not "one class": it is every stale create in flight, up to old capacity − count. Example: 12 active, old capacity 15, 2 selected, target 10 → up to 13 against 10. The surplus is audited but not resolved. | Restate the bound; the operator resolves the surplus. |
| F6-03 | §7.3 step 2; rule 7a | The retry path can lower a stamp that a consumer already raised (for example after a provider cancel), which reopens window (d). | In the retry path, set max(non-null stamp, schedule version). |
| F6-04 | §7.3 step 6; §7.6 | The over-limit check needs the new capacity, which the suspension event payload does not carry. | Add `new_capacity` to the payload, or have BE1 read Billing under the lock. |
| F6-05 | §7.3 steps 2 and 6; §2; §8; §11 | No BE1 audit store was found for the two audit events; the sink is an unmarked NEW item. B-5 delivers a key-based use case with no route (routes are deferred). | Mark the audit sink NEW in §2. State how B-5 invokes the use case. |
| F6-06 | §7.3 step 2 | Undefined outcomes:<ul><li>A same-key retry after the schedule has been applied gives a false 409 and a spurious audit event.</li><li>Repeated audit events are not de-duplicated.</li><li>A second downgrade with a different key while a schedule exists.</li></ul> | Define the post-effective replay; de-duplicate per change group ref; define the different-ref case. |
| F6-07 | §4 step 6; §7.6; §6 | <ul><li>The per-process cap covers creates only, not downgrade or consumer lock-waiters.</li><li>The outbox publisher runner and cadence are unnamed, so "closes when consumed" has no time bound.</li><li>Outbox keys differ: §6 uses (subscription, event type, boundary time); §7.6 uses (organization, event type, `capacity_version`).</li></ul> | Extend the cap to all lock-waiters; name the runner; unify the key. |

## F5 findings (reviewer)

| Finding | Status | Note |
|---|---|---|
| F5-01 | partly | Lost response after commit: closed. In-flight timeout: open (F6-01). 5f bound understated (F6-02). Retry path sound apart from F6-03 and F6-06. |
| F5-02 | resolved | Small retry-path gap: F6-03. |
| F5-03 | resolved with notes | F6-04, F6-07. |
| F5-04 | resolved | Cap scope: F6-07. |
| F5-05 | resolved | — |
| F5-06 | resolved | — |

## Checks (reviewer, paper analysis)

**Interleavings that held:**
- Lost response after the Billing commit.
- Billing refused, or never committed.
- A stale pre-schedule answer meeting a raised stamp.
- A read after the schedule commit.
- Rule 7b with null.
- A null-stamp create after its re-read is used (503).
- Rule 7a for schedules made through the downgrade use case; provider bumps are residual (d).
- Lock order BE1 → Billing.
- Same-key retry while the count still fits.

**Interleaving that failed:** the in-flight timeout (F6-01).

**Other checks that passed:**
- SRS lines and D-066-63 quotations are verbatim.
- 404/403 is deferred to O-CONV.
- The payment boundary is intact.
- No implied approval; owner recording of residuals (d) and (f) is a precondition in §12.
- No local absolute paths.
- Slices B-1, B-2 and B-5 match §4, §7.3 and §7.6.

## Not verified (reviewer)

- Real PostgreSQL behaviour and isolation level.
- Python and driver cancellation semantics for a call timeout.
- The owner's chat selections, and D-171 item 11 (taken from the prompt).
- The register's Billing rows.
- Alembic multi-head impact.
- The outbox publisher infrastructure, which does not exist yet.

## Disposition by the coordinating session

Draft 6 is not edited. The owner-granted extra round is used. The next step is the owner's choice.
