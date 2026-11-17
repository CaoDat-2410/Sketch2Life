# FEAT-027 decisions

## D-027-01 — Normalize before validating

Accepted. The real CLI may apply a bounded, deterministic normalization pass;
the default adapter remains strict for tests and non-demo callers.

## D-027-02 — Drop unsafe optional claims

Accepted. A malformed relation/theme/region is dropped rather than assigned a
guessed reference or geometry. The final payload is then validated as a whole.

## D-027-03 — No case-specific fixture

Accepted. Case 02 must pass using only the actual model output plus generic
normalization rules.
