# BE2-07 → BE2-09 cross-lane X02 review — 2026-10-20

## Result

**X02 remains `NOT_IMPLEMENTED`: the producer event exists, but BE2-09 has no
adopted receiver that applies it to the exact dependent review/playback output.**
The integration must not mutate a BE2-09 fake or treat eventual event presence as
proof that a previously valid playback decision is blocked.

## Source findings

- BE2-07 emits `KnowledgeSupersededV1` from the same producer unit of work as a
  bundle edit (`application/services/knowledge_bundle.py:523`). The event pins
  the exact old and new bundle versions and hashes and is stored via the
  producer's `add_event` port. Its current schema is `0.1-candidate`
  (`contracts/schemas/knowledge_bundles.py:450-464`).
- `RecordingKnowledgeConsumer.apply` records the exact superseded reference and
  deduplicates event IDs (`infrastructure/knowledge_bundle/adapters.py:228-255`),
  but its own docstring says it provides no consumer-held lease/fence. It is a
  BE2-07 fixture projection, not an adopted BE2-09 sink.
- BE2-09's public review lifecycle can resolve/check current source authority and
  change its own review head (`application/ports/video_review_lifecycle.py:65-118`).
  Its transaction has no operation for applying a BE2-07 invalidation to an
  exact dependent target. `VideoReviewLifecycleService.apply` only applies a
  Teacher review change (`application/video_review_lifecycle.py:42-95`).
- The BE2-09 playback port requires current source/review resolution and held
  invalidation fences at dispatch, but the actual adopter is explicitly open
  (`application/ports/video_playback.py:16-38`). No composed implementation
  shows that the producer event reaches that fence or prevents playback after
  supersession.

## Required owner/card adoption

BE2-09 needs an adopted public boundary for either (a) receiving the exact
`KnowledgeSupersededV1` event idempotently and recording invalidation against
the exact dependent review/playback target, with the BE2-07 validity fence held
through the consumer commit and each playback dispatch/fetch; or (b) resolving
current BE2-07 eligibility at every review/playback action under that same held
fence. The owner must also define the exact bundle-to-video lineage and replay,
duplicate, and lost-delivery behavior. Until then X02 stays
`NOT_IMPLEMENTED`; no synthetic consumer mutation or card-owned contract change
is authorized by this review.

## Verification and scope

This is a source-contract review only. No tests were run because no X02 behavior
was composed; no production or card-owned code was changed. The source files and
their SHA256 values are in `../metrics/CROSS_LANE_X02_20261020.json`.

The Modal result for X01 plus adjacent BE2-07/08 regression remains 296/296
passing. That result does not exercise X02 and does not change X01's `PARTIAL`
state or FEAT-057's overall `PARTIAL` state. No card acceptance/status or
runtime gate changed; nothing was staged, committed, pushed, or merged.
