# FEAT-066 L2 Billing contract Draft 2 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction; started on the owner's instruction "Review Draft 2". Scratch folder `tmp/feat066-billing-review-d2/` created and left empty; read-only Git only (`rev-parse`, `log`, `status --short`).
- **Pin reviewed:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT2_20261118.md`, 22,639 bytes, SHA-256 `D5FBB6AA820447F3E94349A722163EB4C18149BC7A3A3AF162A99362338C7D9E`. Draft 1, the Draft 1 review record, the questions document, roadmap Draft 4, the adopted SRS and the register matched; local `origin/dev` = `1c9148e8`.
- **What the reviewer did not do (its statement):** no file changed; no test, validator, build, app, Docker, database, network or fetch; neither the gate secret directory nor the local database URL file opened.
- **Verdict:** NOT READY — **P1=0, P2=9, P3=12**. The P1 and P2 count did not fall (9 in Draft 1, 9 in Draft 2). Nothing unsafe is authorized; payment stays limited to three commands and empty tables; NEW items and interpretations are listed. The draft fails its own criterion 3: recovery paths of the cross-module class-create flow can free a slot of a live class or cannot be replayed, and the lifecycle lacks inputs and triggers B-1 and B-2 need.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| N-01 | Reconcile can release the slot of a class confirmed in Billing but not yet committed in BE1 (invisible to `ActiveClassListPortV1`); BE1 releasing after an ambiguous commit can free a slot of a class that exists | Reconcile releases only `CONFIRMED` rows older than a safety age; BE1 never releases on an ambiguous commit |
| N-02 | At a downgrade's effective time reconcile can re-add slots for selected classes that BE1 has not yet projected read-only, undoing the downgrade | Reconcile excludes classes in an applied change group, or the BE1 port returns suspension state |
| N-03 | Same-key replay undefined for `RELEASED`/`EXPIRED` reservations (normal retry blocked), for a `CONFIRMED` reservation whose class BE1 rolled back, and for a concurrent duplicate finding `HELD` | Define re-open or fresh reservation; BE1 reuse or release-and-re-reserve; duplicate outcome |
| N-04 | A BE1 transaction stays open across two Billing calls with no lock or statement timeouts and no pool bound; under load creates can starve Billing's connection (no deadlock cycle as drafted) | `lock_timeout`/`statement_timeout` mapping to `BILLING_UNAVAILABLE`; bound on lock hold; separate pool or concurrency bound |
| N-05 | `grace_until` = period end + 7 days shortens grace when failure is reported after period end; "period end with no renewal → GRACE" is an unmarked extension (SRS §23.3) | max(failure time, period end) + 7 days, or mark as interpretation |
| N-06 | The next period's `paid_extra_slots` has no source: `schedule_downgrade` has no target add-on count and `record_renewal_outcome` carries none; carry-over at renewal or local auto-renew unstated | Add the target count; rule: scheduled target, else renewal input, else 0 |
| N-07 | Time-based effects with BE1-visible consequences (downgrade release and suspension event, local roll-over, GRACE → RESTRICTED) have no trigger if no command runs | A settle routine at the start of every command and a periodic sweep for outbox emission |
| N-08 | Existing organizations never get a subscription (no operation enumerates them; Billing cannot read BE1); a bootstrap failure between organization commit and `open_subscription` has no repair path | B-1 operation to open subscriptions for all existing organizations (re-runnable); idempotent bootstrap retry; re-run reconcile at B-2 enablement |
| N-09 | What confirm re-checks under the lock (status as well as capacity) and the public result for `EXPIRED` are unspecified | Re-derive status and capacity; map `EXPIRED` to 409 or 503 |

## P3 findings (summary)

N-10 `change_group_key` duplicates the register's `capacity_change_group_ref_optional`; uniqueness must be (group, class). N-11 `read_balance` before the first admission of the month unspecified (derive without writing, or create under lock). N-12 unmarked NEW storage: request fingerprint on usage, nullable actor/operation/key for `BACKFILL`, content hash for payment commands, relation of `payment_event_ref` to `provider_event_receipts`, `billing.outbox` columns. N-13 `activate_add_on_slots` lacks `prorated_amount`; event types not enumerated; a unique on `payment_event_ref` alone blocks several rows per event. N-14 no command/route for auto-renew on/off or downgrade requests; `CANCELED_BY_PROVIDER` mapping per state. N-15 the local auto-renew guard must name `env in {local, test}` and drop "synthetic" (bootstrap is the production tool); state what a production organization gets at first period end. N-16 organization scope with no subscription in `admit_video_request`. N-17 class-create replay returns the original 201 only (errors are re-evaluated); name `INVALID_IDEMPOTENCY_KEY`. N-18 the placeholder price version belongs in an env-guarded seed, not an unconditional migration; `approved_by`. N-19 reservation expiry default and a per-actor cap on `HELD` rows (D-066-63 asks for expiry and recovery). N-20 while a downgrade is scheduled, reserve against the lower capacity. N-21 the SRS billing actor is "admin billing", not "School Manager" — mark as interpretation.

## F-01 to F-20 (reviewer)

Resolved: F-03, F-05, F-06, F-07, F-08, F-10, F-11, F-12, F-14 (with N-10), F-17, F-18, F-19, F-20. Resolved with gaps: F-04, F-13. Partial: F-01 (N-01, N-03, N-09), F-02 (N-08), F-09 (N-05, N-07, N-15), F-15 (N-07), F-16 (N-06, N-07, N-20). Checks with no finding: the video-quota scope lock and lazy grant; the lifecycle against §23.3 apart from N-05; the payment boundary; status codes against §9.8; slices and gates; source facts (organizations only from `be1_bootstrap.py`; `be1_classrooms.state` default `active`; no Billing code or branch label; BE1 has a session command-receipt pattern but none for class create).

## Not verified (reviewer)

The owner's chat selections; SRS header provenance; Alembic multi-head test impact; runtime behaviour; whether Billing would share BE1's engine.

## Disposition by the coordinating session

Draft 2 is not edited. Because the P1 and P2 count did not fall and most remaining P2 findings come from the cross-module reservation design chosen in Q-L2-2, the coordinating session returns the design choice to the owner before a Draft 3.
