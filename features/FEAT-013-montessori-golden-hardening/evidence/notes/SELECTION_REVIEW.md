# Golden selection and baseline review

- Date: 2026-08-25
- Result: PASS
- Selection: 20 records, exactly five in each of `0-3`, `3-6`, `6-9`, and `9-12`.
- Parent: FEAT-002 v1 at recorded parent commit `2d61528`.
- Integrity: every selection stores base ID, version, record SHA-256, and source-file SHA-256.

The selection matches revision 1 exactly. All FEAT-002 file hashes still match the approval-time freeze. Golden records are versioned full derived records under `data/activity-catalog/golden/v1/`; no v1 artifact is overwritten. A deliberate parent-file mutation returns non-zero, proving that silent baseline drift is rejected.
