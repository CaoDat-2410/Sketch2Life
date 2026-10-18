# BE2-09 planning decisions

## C2b — invalidation archives; rebind never copies approval

One monotonic canonical review revision across subject changes; immutable old
entry/history retained. Revocation strengthens stale state. Authorized restoration
of same exact subject opens empty head and needs NEW review, not revival of old
approval. Pin hash can change for policy epoch; require authenticated owner cause,
not inferred script edit. Key namespace conflicts across review/change writes.
Historical event result not current permission; real source-owner/access/dispatch
fences CR09-01/02 still mandatory, outbox or local mock not actual playback stop.

## C2a — immutable receipt is historical, replay response is current applicability

Own review CAS/head/history/shared-record/receipt/audit/outbox is one transaction
port, current action fences held through commit. Lost commit ACK is unavailable,
not rollback; replay original key under current authority. Original stored record
is immutable, response state derives from current head so a superseded approval
doesn't appear effective. Canonical head mismatch/external history not silently
imported; version-rebind protocol CR09-01 still required. No08 row rewrite.

## C1b — original-key receipt recovery is not current playback permission

Persist intent before external effect, do not keep own DB transaction across BE1
start. Use explicit recoverable protocol; no two-commit atomicity claim. Missing/
ambiguous receipt never triggers implicit resend or false rollback. Confirmed
response is historical reference only, not current player status/access URL. Actual
BE1 current session CAS/review/consent/deadline/access-use fencing remains CR09-02;
MEMORY transactions/synthetic receipts don't prove durable races or authentication.

## C1a approved implementation —2026-10-18

Actual owner approves exact revision1 P1–P4. Reuse shared24, owned native binding
only; media hash distinct from pin digest.09 head candidate is not08 SQL mutation
or canonical adoption. Audience/consent order normalized and duplicates rejected.
Invalidation preserves historical entry, prevents revival of that head. Pure
permits_intent is not current Teacher/consent/moderation/access authority or playing.
Actual guards/receipts/adoption still required; no shared/foundation migration edits.

2026-10-18 D01: owner routing/batch approval ->plan only; exact revision1 pending.
D02: reuse05 shared24 session_content, not a duplicate review schema/liveSketch gate.
D03: approved !=playing,08 media hash !=pin/catalog hash, review CAS !=job/run/session.
D04: own09 canonical review head + combined08 projection require CR09-01, because
08 row participant freezes review_revision. Do not rewrite08 lineage/migrations.
D05: actual session/access outcome requires adopted receipt protocol CR09-02;
timeout/fixtures not actual playing. Real owner wiring remains teammate-deferred.
D06: local/source-pinned component first, delayed actual runtime batch. No waiver
of full acceptance or actual provider/budget/provisioning approval implied.
