# BE2-09 planning decisions

## FEAT-057 implementation-scope addendum — 2026-10-21

- Approved addendum: plan/CROSS_LANE_BE2_09_SCOPE_DRAFT_20261021.md
- Approval record: approvals/TASK_APPROVAL.md
- Proposed scope is CR09-01 only: review-owned canonical head and projection bound to the exact BE2-08 artifact. It does not edit BE2-08/BE1 rows or close CR09-02.
- Owner approved the exact scope SHA256 121699BE6A3134C65EF16917941FA75F00401EA18462BA929C2E897BCAB46285. The verbatim approval is in approvals/TASK_APPROVAL.md. The minimal execution file subset must be recorded before edits.
- X05d remains BLOCKED until an already-adopted current-source resolver/fence exists. The approval does not authorize X02, session/access integration, or playback runtime.

## FEAT-057 cross-card owner response — 2026-10-21

The user confirmed they own the affected cards and approved the G0 proposal
with `Chốt theo đề xuất`. For BE2-09, B5/CR09-01 is `ADOPT_WITH_CHANGES`:
BE2-09 owns the canonical review head and DATA-27 projection bound to the exact
committed BE2-08 artifact hash/version; do not rewrite BE2-08 rows or migrations.
B6/X05d is `BLOCKED` because no already-adopted current-source resolver/fence
covering review commit and playback intent was identified; do not pull X02 into
this slice. CR09-02 remains open. See FEAT-057's
`evidence/notes/G0_CARD_OWNER_DECISION_BALLOT_20261021.md`.

This adopts contract direction only; implementation approval, actual
session/access adoption, card status, and acceptance are unchanged.

## C4b — actual own SQL evidence is separate from integration acceptance

Owner separately approves own temporary PG17 environment, exact21 tests/cleanup
and checkpoint. Actual21 PASS under loopback limited nonsuperuser; source unchanged,
no code change. Temporary cluster/binary/archive/secrets removed. Local pack remains
SQL collection-only, its NOT_RUN label does not overwrite separate E07 actual PASS.
Own durable transaction/CAS/trigger/reconnect evidence does not prove actual BE1/
source authority, cross-owner session receipt or each-use gateway; CR09-01/02 OPEN.

## C4 — finish internal scope without micro-checkpoint approval stops

Owner explicitly approves continuous remaining P3/P4 implementation, tests and
handoff. Internal COMPLETE_LOCAL_VERIFIED does not relabel full09 DONE. Next gates
are actual SQL, actual owner/session/access adoption and selected08 runtime/consumer
acceptance; not another internally authorized code checkpoint/new-card approval.

CMD-41 reuses shared24 +strong quoted own review If-Match. CMD-42 uses strict own
target/hash/subject digest/review refs +body expected_session_revision; rejects
If-Match rather than confusing axes. Exact subject resolved server-side, including
historical originals for recovery; application rechecks actual current fences.
Responses revalidate exact native outputs, contain historical receipt status only,
no URL/access grant/current playing. No default auth/production mounting.

Local one-batch source/node-pinned runner reuses existing exact JUnit classifier,
drops09/08 SQL opt-ins, SQL collection-only. Broader21 prepared PG cases not run;
458 own +1894 regression PASS does not stand for real DB/identity/gateway effects.

## C3a — owned storage is neither current authority nor cross-owner atomicity

Independent video_review schema; six tables and new branch migration, no08/BE1
writes/FKs or published migration edits. Closed JSON type graph rechecks native
domain invariants and relational scope. Review/change share actor/key namespace;
playback namespace org/session/actor/key excludes video to catch changed-target
reuse. Own session advisory lock serializes first insert/CAS, not BE1 revocation.
History/receipts/events append-only, playback pending1->terminal2 only. Audit event
is minimal committed intent, not a delivered notice or actual session receipt.
Prepared10 PG cases need separate VR09 disposable loopback PG17 opt-in/approval;
local mock/offline70 PASS does not prove actual durable transactions/races.

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

## Owner-directed BE2-08 artifact read-model disposition — 2026-10-21

The owner directed BE2-08 to publish a public, read-only finalized-artifact model
for BE2-09. BE2-09 must bind its own review head/projection to the exact artifact
identity and must not update BE2-08 rows or migrations. Exact fields, terminal
visibility and adoption remain to be agreed with BE2-08 before the CR09-01
manifest is frozen.

X05d remains BLOCKED; this direction does not create an already-adopted
current-source resolver/fence or authorize a bypass. X05c/CR09-02 remains OPEN;
no session-start, current access or playable-media claim follows from the
read-only artifact model. No source/test/status/acceptance changed.
