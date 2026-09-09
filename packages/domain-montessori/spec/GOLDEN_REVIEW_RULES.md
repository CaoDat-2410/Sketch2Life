# Golden Catalog review rules

## Record review

For every golden activity, the reviewer checks:

1. The base ID/version/checksum points to the intended FEAT-002 record.
2. Age guidance is narrower but not represented as a developmental diagnosis.
3. Readiness is directly observable and can be encoded in fixture input.
4. Materials are concrete, locally understandable, and include suitability plus prohibited alternatives.
5. Presentation, child work, restoration, isolation of difficulty, and control of error are specific to the activity.
6. Safety covers actual material/environment hazards and explicit stop conditions.
7. Primary/secondary objectives and progression links preserve identity and form no cycle.
8. Variants change support/complexity only; no hard rule is weakened.
9. Completion evidence is descriptive and non-evaluative.
10. Status remains provisional and `production_eligible=false`.

## Automated rejection

The validator rejects:

- changed FEAT-002 baseline hashes or mismatched base-record checksums;
- missing/duplicate IDs, invalid versions/references, or progression cycles;
- full-band age windows, non-observable readiness, or missing readiness;
- duplicate complete presentation/safety blocks;
- placeholder substitute text such as `_APPROVED_SUBSTITUTE` or “vật liệu tương đương”;
- missing primary/substitute/suitability/prohibited material data;
- missing activity-specific safety or 0-3 caregiver/direct-supervision rules;
- variant activity/objective identity drift;
- production eligibility or premature owner-review claims;
- fewer than 60 fixtures, missing category coverage, checksum mismatch, or wrong expected result.

Automated passing proves contract and fixture quality only. It does not certify Montessori pedagogy, child outcomes, legal compliance, or production safety.
