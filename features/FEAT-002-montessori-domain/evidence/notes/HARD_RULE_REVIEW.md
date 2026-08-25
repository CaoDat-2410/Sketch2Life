# Hard-rule review

- Date: 2026-08-25
- Tasks: P1-06 through P1-09
- Result: PASS

Eight hard rules cover activity status, minimum/maximum age, readiness, prerequisite, supervision, policy, and material availability. The harness retains all applicable reasons and returns `NO_VALID_ACTIVITY` when no candidate survives.

Twenty-four fixtures pass: 12 positive and 12 blocked/no-result. Coverage includes all four age bands, inclusive boundaries, multiple valid candidates, approved material substitutes, prerequisites, inactivity, age, readiness, safety, caregiver policy, materials, multiple failures, and no-valid outcomes.

The mutation test changed an expected allowed ID and correctly returned non-zero because the manifest checksum no longer matched. This demonstrates that fixture evidence cannot be silently edited without detection.
