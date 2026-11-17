# BE2-01–14 cross-lane residual review — 2026-10-20

## Result

X04–X09 remain `NOT_IMPLEMENTED` under the current FEAT-057 approval. The
source has candidate producer/consumer ports, but each edge still lacks either
an adopted binding, a real cross-card commit boundary, or the exact consumer
event/lineage required by the plan. The detailed source hashes are in
`../metrics/CROSS_LANE_RESIDUAL_REVIEW_20261020.json`.

## Edge findings

| Edge | Review result | Missing boundary / next gate |
|---|---|---|
| X04 — BE2-12 publication → BE2-09/11 | `NOT_IMPLEMENTED` | `ContentConsumerQueries.resolve_reference` returns a current, exact **metadata reference**. The `PublishedContentQueryPort` has no call site in the consumer application modules. BE2-09 review and BE2-11 activity execution require their own exact target/current-authority checks; no adopted adapter maps the publication reference into both consumers or carries recall/audience invalidation through their commit fences. Card owners must adopt that binding. |
| X05 — BE2-08 output → BE2-09 review/playback | `NOT_IMPLEMENTED` | `VideoCreateService.create` accepts a newly queued run only when it has no artifact. The worker exposes an `AtomicVideoFinalizer` candidate protocol, but the actual foundation/job/run/artifact adopter is open. BE2-09 therefore has no accepted exact output lineage to review or play. Resolve the atomic BE2-01/08 finalization adoption first. |
| X06 — BE2-08 failure → BE2-10 disposition | `NOT_IMPLEMENTED` | BE2-08 has a typed `VideoWorkerOutcome` and BE2-10 has `FailureBridge`, but no adopted bridge maps an authenticated exhausted BE2-01/08 lifecycle into the exact `FailureTarget`. The bridge contract itself requires atomic/recoverable owner effect and bounded retry consumption. Card-owner adoption and a typed delivery/receipt seam are required. |
| X07 — BE2-13 preset → BE2-01 job | `NOT_IMPLEMENTED` | Preset `dispatch` runs an explicit `SessionCommands` effect. That port is BE1-owned session compare-and-apply, not a BE2-01 job creation/dispatch contract. No approved adapter converts an immutable preset intent into one exact foundation job while holding policy/disable-generation fences. |
| X08 — BE2-14 policy → BE2-03/04/08/13 | `NOT_IMPLEMENTED` | BE2-14 has current-use lease contracts, but the reviewed consumer services do not bind them. The BE2-14 boundary requires a durable current owner adapter; policy eligibility also does not imply budget reservation or worker authorization. Adopt consumers individually through their card-owned policy ports before composing. |
| X09 — BE2-01 job/attempt → BE2-08/13 | `NOT_IMPLEMENTED` | The foundation `AiJobService` and generic `DispatchWorker` are present, and BE2-08 has its own candidate worker. No shared handler registry/adopter routes exact job types and preserves attempt/subject/artifact lineage into both BE2-08 and BE2-13. BE2-13 also has no foundation worker entrypoint in this candidate. |

X02's separate source review is in `CROSS_LANE_X02_REVIEW_20261020.md`;
X03's exact BE2-12-reference-to-BE2-08-library mapping blocker remains in
`CROSS_LANE_X01_REVIEW_20261020.md`. X01 remains `PARTIAL` after its 296/296
Modal run because it does not commit the foundation job and BE2-08 artifact.

## Recommended next step

Do not rerun the Modal notebook. The next useful action is an owner decision
package for the missing card-owned adoptions: first the X05 atomic BE2-01/08
finalization seam (which also unblocks X06 and strengthens X01), then X02/X04
source-publication delivery, then X07/X08/X09. The current FEAT-057 approval
allows FEAT-owned adapters only when existing public contracts suffice; it does
not authorize changes to card-owned contracts or implementations. Until the
owners adopt those seams, retain the current `PARTIAL`/`NOT_IMPLEMENTED` states.

## Verification and scope

Source review only; no behavior tests were run and no production/card-owned
source was changed. Validators and `git diff --check` passed after recording
this review. FEAT-057 remains `IN_PROGRESS`; no card acceptance, runtime gate,
commit, push, merge, or deployment changed.
