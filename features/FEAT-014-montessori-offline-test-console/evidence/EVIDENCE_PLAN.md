# FEAT-014 evidence plan

| Evidence ID | Tasks / criteria | Planned evidence | Interpretation |
|---|---|---|---|
| EV-C1-01 | C1-01 / AC-C1-01..03 | `metrics/baseline-hashes.json`, `notes/CONTRACT_REVIEW.md` | Inputs and no-ranking boundary are frozen |
| EV-C1-02 | C1-02 / AC-C1-03..04 | `metrics/fixture-parity.json`, `raw/parity-tests.txt` | Shared evaluator preserves all 74 outputs and reason order |
| EV-C1-03 | C1-03 / AC-C1-01..05 | `raw/cli-tests.txt`, committed scenario fixtures | List/evaluate/replay behavior and exit codes are reproducible |
| EV-C1-04 | C1-04 / AC-C1-05..06 | `raw/interactive-tests.txt`, `raw/evidence-security.txt` | Guided parity and confined evidence writes pass |
| EV-C1-05 | C1-05 / AC-C1-02,04,06,08..09 | `runs/` examples and negative snapshots | Human-reviewable valid/blocked/error examples exist |
| EV-C1-06 | C1-06 / AC-C1-07,10 | `raw/final-validation.txt`, `notes/TRACEABILITY_REVIEW.md`, `notes/KNOWN_LIMITATIONS.md` | Independence, security, tests, and limitations are verified |

Every implementation claim must include command/input, date, environment, output path, result, interpretation, limitations, and follow-up. Evidence records only fixture IDs/enums/numbers and deterministic outputs.
