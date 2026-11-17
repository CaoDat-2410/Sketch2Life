# FEAT-013 evidence plan

| Evidence ID | Tasks / criteria | Planned evidence | Required interpretation |
|---|---|---|---|
| EV-G1-01 | G1-01 / AC-G1-01..02 | `metrics/baseline-hashes.json`, `notes/SELECTION_REVIEW.md` | Exact parent records selected and baseline preserved |
| EV-G1-02 | G1-02..03 / AC-G1-03..08 | `notes/CONTRACT_SEMANTICS_REVIEW.md`, contract test log | v2 fields and readiness/material/progression/variant semantics are complete |
| EV-G1-03 | G1-04 / AC-G1-03..07 | `notes/REVIEW_0_3.md`, batch metrics | Five 0-3 records are specific, caregiver-safe, and reviewable |
| EV-G1-04 | G1-05 / AC-G1-03..07 | `notes/REVIEW_3_6.md`, batch metrics | Five 3-6 records pass depth and safety checks |
| EV-G1-05 | G1-06 / AC-G1-03..07 | `notes/REVIEW_6_9.md`, batch metrics | Five 6-9 records pass depth and progression checks |
| EV-G1-06 | G1-07 / AC-G1-03..07 | `notes/REVIEW_9_12.md`, batch metrics | Five 9-12 records pass depth and progression checks |
| EV-G1-07 | G1-08 / AC-G1-09..10 | `raw/harness-run.txt`, `metrics/fixture-coverage.json` | 60+ fixtures pass offline and deterministically |
| EV-G1-08 | G1-08 / AC-G1-02,10 | `raw/deliberate-failure.txt`, `raw/baseline-mutation.txt` | Expected mismatch and parent mutation both fail non-zero |
| EV-G1-09 | G1-09 / AC-G1-11..12 | `notes/OWNER_REVIEW_PACKET.md`, `metrics/traceability.json` | Every record has explicit provisional owner decision and evidence links |
| EV-G1-10 | G1-10 / AC-G1-12..13 | `raw/final-validation.txt`, `notes/KNOWN_LIMITATIONS.md` | Architecture/security/reproducibility pass without overclaiming production readiness |

Every implementation evidence item records command/input, date, environment, output path, reviewer, result, interpretation, limitations, and follow-up. Evidence never contains real child data, secrets, accounts, or machine-local absolute paths.

## Execution status

| Evidence ID | Status | Artifact |
|---|---|---|
| EV-G1-01 | PASS | `metrics/baseline-hashes.json`, `notes/SELECTION_REVIEW.md` |
| EV-G1-02 | PASS_AUTOMATED | `notes/CONTRACT_SEMANTICS_REVIEW.md`, unit tests |
| EV-G1-03 | PASS / OWNER_ACCEPTED_PROVISIONALLY | `notes/REVIEW_0_3.md` |
| EV-G1-04 | PASS / OWNER_ACCEPTED_PROVISIONALLY | `notes/REVIEW_3_6.md` |
| EV-G1-05 | PASS / OWNER_ACCEPTED_PROVISIONALLY | `notes/REVIEW_6_9.md` |
| EV-G1-06 | PASS / OWNER_ACCEPTED_PROVISIONALLY | `notes/REVIEW_9_12.md` |
| EV-G1-07 | PASS | `raw/harness-run.txt`, `metrics/fixture-coverage.json` |
| EV-G1-08 | PASS_EXPECTED_NONZERO | `raw/deliberate-failure.txt`, `raw/baseline-mutation.txt` |
| EV-G1-09 | PASS / OWNER_ACCEPTED_ALL_PROVISIONALLY | `approvals/OWNER_CONTENT_REVIEW.v1.json`, `notes/OWNER_REVIEW_PACKET.md`, `metrics/traceability.json` |
| EV-G1-10 | PASS / FEATURE_CLOSED | `raw/final-validation.txt`, `notes/KNOWN_LIMITATIONS.md` |

All feature closure evidence is complete. Project-owner acceptance is provisional and is not interpreted as qualified pedagogical or production approval.
