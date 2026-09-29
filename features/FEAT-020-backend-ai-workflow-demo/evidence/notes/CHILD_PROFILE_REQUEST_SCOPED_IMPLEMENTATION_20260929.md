# Child-profile request-scoped recommender — implementation evidence

- Date: 2026-09-29
- Status: partial implementation under the approved integrated FEAT-018/020/030 plan.
- Data: only reviewed catalog fixtures and synthetic request-contract tests; no real child data.

## Behavior implemented

- `ChildLearningProfileContextV1` and `P1ContextOptionsRequestV1` validate bounded interest/dislike
  identifiers, adult-confirmed activity/objective progress, readiness, materials, supervision and
  explicitly selected non-clinical supports.
- The existing profile-free GET context-options route is preserved. An additive POST on the same
  route checks the existing actor/session/version gates and uses the supplied profile for that
  request only.
- The response includes baseline and personalized recommendation IDs/cards, rank-change status,
  bounded signal counts and exclusion counts. The request does not advance session version or call
  the vision/Qwen provider again.
- The declared caregiver/guide role and profile timestamp are returned as provenance; adult-confirmed
  progress evidence retains the confirming role/date and is disclosed in a card explanation only
  when it influences ranking.
- A regression exposed an empty recommendation-card list when profile ranking chose a golden
  activity version without curated expansion metadata. The adapter now renders only exact-version
  authored metadata and surfaces a blocked preparation warning instead of borrowing another
  version's preparation record.
- Profile mode applies supervision, adult-confirmed prerequisite, dislike, readiness and every
  required material group as hard gates; interests, confirmed objective progression and explicit
  supports affect deterministic ranking only after gates. No-profile behavior remains unchanged.
- No profile storage, history write, catalog entry, authentication mechanism or provider call was
  added. Future persistence is explicitly deferred in ADR-0010.

## Catalog evidence

`backend/tools/audit_child_profile_catalog.py` reports revision `catalog-2026-09`: 300 reviewed
semantic profiles, 94 scene concepts and 20 learning objectives; no child preference/history records;
readiness metadata on 100/300 templates; materials and supervision on 300/300; 14 templates declare
prerequisites; 40 material registry options; zero explicit support tags. No catalog rows were
invented. Missing readiness/material metadata excludes that activity only when profile filters are
active. MVP required material groups are preserved individually; `ACT-0002` regression coverage
proves one available item must be confirmed from each of its two required groups.

## Verification

- Full backend test suite and focused profile/P1/topic/SAM/contract/metadata regression suite passed
  from the repository root. Environment-gated tests were skipped as configured.
- Changed Python files pass Ruff. Security validator reports `REPOSITORY_SECURITY_VALID` (8,563
  publishable files; no absolute machine paths or forbidden secrets).
- See FEAT-018's
  [`INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_IMPLEMENTATION_20260929.md`](../../../FEAT-018-live-image-canvas-flow/evidence/notes/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_IMPLEMENTATION_20260929.md)
  for mobile/UI evidence and pending Android acceptance. See ADR-0010 for the session-only boundary.
