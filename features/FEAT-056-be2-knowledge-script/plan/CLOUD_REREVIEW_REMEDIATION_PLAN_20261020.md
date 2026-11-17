# BE2-07 cloud re-review remediation plan — default-ignorable word separators

- Status: APPROVED / IN_PROGRESS.
- Authority: `../approvals/CLOUD_REREVIEW_REMEDIATION_APPROVAL_20261020.md`, within the
  approved P3-N1 follow-up (`P3_CLOUD_FOLLOWUP_PLAN_20261020.md`). Revision 1 stays frozen.
- Starting snapshot: `1d731c53ac48305d07c69c5cbf810ab80cca6559`.

## Finding (P3-R1)

The P3-N1 correction removes Unicode 15.0 Default_Ignorable_Code_Point and Cf characters
before comparison. That covers a character inserted inside a word. It does not cover the
same characters used in place of a space: removal joins the neighbouring words into one
token. Hangul fillers (U+115F, U+1160, U+3164, U+FFA0) usually render as a blank gap, so
`"Mèoㅤcóㅤcánh."` looks like the imagined literal `"Mèo có cánh."`. It currently
passes the domain helper, the strict record DTO and the real edit handler (200,
`generation_ready`, and an exact export that carries the imagined sentence as a fact).

## Correction

This changes the comparison only, in `domain/knowledge_bundle.py`:

- Compute each literal signature twice, once with default-ignorable/Cf characters removed
  (the existing behaviour) and once with them replaced by a word separator.
- Report an overlap when any pairing of claim and imagined variants overlaps.
- Keep the ignorable removal before NFKC, so CGJ between a Vietnamese base and its accent
  still composes in the removal variant.
- Stored text, projections, canonical bytes, control validation and the DTO call path do not
  change.

## Acceptance

- New regressions fail before the correction and pass after it:
  - domain, both directions, for each Hangul filler and a zero-width separator;
  - strict record DTO;
  - real edit handler with a full-store/commit-count check.
- Existing inside-word, Vietnamese accent, token-boundary, empty-signature, control and
  preservation tests still pass.
- The six task07 modules, Ruff, strict mypy and the repository validators pass.
- Historical evidence, maps, metrics and the cloud-review export stay unchanged.
- Codex performs the independent post-push review. Component NOT_ACCEPTED; card
  IN_PROGRESS / NOT_DONE.
