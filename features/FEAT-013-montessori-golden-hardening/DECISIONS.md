# FEAT-013 decisions

- Optimize 20 records, five per age band, before considering catalog expansion beyond 100.
- Preserve FEAT-002 v1 unchanged; every hardened record references its base activity ID/version and receives a candidate version 2.
- Use full replacement records in the golden overlay, not implicit merge patches, so reviewers and tests see the complete effective artifact.
- Treat exact age windows as eligibility guidance subordinate to observable readiness and safety constraints.
- Readiness descriptions must be observable and non-diagnostic.
- Every required material group needs a concrete primary option and a concrete household substitute with suitability/safety constraints; placeholder-only substitute IDs fail review.
- Each golden activity needs activity-specific setup, presentation, child work, restoration, control-of-error, hazards, supervision, and stop conditions.
- Record one primary objective and zero to two secondary objectives; identity/version remain explicit for later Gate B.
- `NO_VALID_ACTIVITY` remains valid and hard rules are never relaxed to surface a golden record.
- No ranking weights, AI mapping, UI, API, persistence, or integration code belongs to this feature.
