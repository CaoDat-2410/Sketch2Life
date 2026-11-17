# Montessori console scenarios

Closed-schema synthetic examples for FEAT-014. They contain only versioned activity IDs, numeric age, readiness/prerequisite/material IDs, supervision, policy, and candidate status. Free-form child data is forbidden.

- `valid-primary.json`: primary material, exit 0.
- `valid-substitute.json`: household substitute, exit 0.
- `blocked-multiple.json`: four ordered blockers, exit 2.
- `malformed-unknown-field.json`: deliberate unknown child-data field, exit 1.
