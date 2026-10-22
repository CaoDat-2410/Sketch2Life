# BE2-08 planning context

## Current checkpoint: Claude D3 rereview follow-up - 2026-10-21

Claude verified all 81 D3 review-manifest entries, closed the two prior P2 findings in draft, and found one new P2 (completion-time BUDGET_EXCEEDED) plus four P3 items. Report: FEAT-057 evidence/notes/CROSS_LANE_UOW_CLAUDE_D3_REREVIEW_REPORT_20261021.md, SHA256 92BE229378A2DE06BAEED1FC6F675EA15FED338892A002A833F81F6972B44C12.

Successor drafts: FEAT-044 foundation Rev7, budget CR Rev2 and stale CR Rev2; FEAT-050 BE2-08 Rev3; FEAT-049 BE2-14 Rev3; FEAT-057 slice plan Rev8. NEW-2 through NEW-5 are clarified in draft. Completion-time resource denial remains a separate D4 owner choice, pending at evidence/notes/CROSS_LANE_UOW_OWNER_D4_COMPLETION_BUDGET_BALLOT_DRAFT_20261021.md.

D3 C1-A/C2-A remain selected. No code, schema, tests, official approval or acceptance changed. D4 must be settled before implementation scope is finalized. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; Modal/Lightning/runtime deferred. Earlier checkpoints below remain historical.


## Current checkpoint: owner D3 recorded, successor review pending - 2026-10-21

The owner explicitly selected C1-A and C2-A with the conditions preserved in FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md (SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C). This supersedes the earlier ballot's PENDING design response; it does not rewrite the historical report or ballot.

Latest candidates: FEAT-044 foundation UoW scope Rev6 plus joint BE2-01/14 budget CR, separate BE2-01 schema CR and stale-finalization CR; BE2-08 scope Rev2; BE2-14 scope Rev2; FEAT-057 slice plan Rev7. They are DRAFT / pending independent review and supplemental S/F/schema approvals, not implementation approval.

C1 holds both job and run QUEUED in durable BE2-01 metadata, excludes budget-wait time from dispatch-loss/retry recovery and rechecks eligibility/reservation before execution. C2 commits SUCCEEDED/STALE, the paired terminal stale run without artifact/ready state, receipt and verified-owned-ref cleanup intent together. BE1 descriptor/quarantine/accepted-reference adoption remains pending; accepted output must be protected.

X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Budget unit/limit, maximum defer duration and deadline action remain PENDING. No source/test/schema/migration/official approval, card acceptance or runtime change follows. Earlier dated entries below are historical checkpoints.


## Current checkpoint: Claude rereview 3 — 2026-10-21

Claude reviewed FEAT-044 scope Rev5 and FEAT-057 plan Rev6 and returned CHANGES_REQUIRED. The correction specification and D3 ballot are prepared under FEAT-057; C1 budget-deferral design and C2 durable stale cleanup are still awaiting the owner. D1/D2 are preserved. No new scope/implementation approval is inferred. S/F are not ready for supplemental approval.

X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Budget unit/limit remain unprovided. No source/test/official approval, acceptance, runtime, or Git publication change is authorized by these drafts.

Earlier dated entries below are historical checkpoints; this entry records the current review state.


## Cross-lane lifecycle participant direction D1 — 2026-10-21

The owner selected paired job/run A/S/B/F boundaries owned by BE2-01's UoW.
BE2-08's participant is limited to BE2-08 video rows and cannot begin, commit,
or roll back the UoW. Reconciler and outbox-driven transitions must include the
participant. Rejected finalization writes quarantine/cleanup intent through a
separate foundation reject commit; rollback is reserved for infrastructure
failure with recovery. This is design direction only: independent review and
separate supplemental approval remain required, CR08-01 is open, and the
existing BE2-08 approval is unchanged. FEAT-057 slice-plan revision 4 alignment
remains open. No test or runtime status changed.

## C4b actual own SQL —2026-10-18

Parent c7b17ac; owner approved separate08 PostgreSQL environment, recorded before
setup. Actual PG17.11 own11 PASS, zero failures/errors/skips;702-file source closure
unchanged, no code fix. Loopback restricted role/no CREATEDB, unique cluster stopped
and data/binaries/archive/secrets removed, receipts retained. Own SQL gate complete;
actual foundation/owner/copy/provider/selected-decoder integration open, whole08
IN_PROGRESS. E09 and updated ACCEPTANCE_AUDIT.md are current.

## C4 continuation —2026-10-18

Owner requested continue; parent d55e9ca. P4 one-command source/node-pinned local
runner,13 real synthetic GIF frame-decode fixtures/rights +24 runner checks and
A1–A8 audit/runtime handoff prepared.459 own +1435 existing=1894 PASS;702-file
source closure unchanged; Ruff/Mypy19/governance PASS. Initial evidence parser/
Ruff-cwd findings retained then fixed and all rerun. SQL11 collection only;
production decoder/provider/owner adoption NOT_RUN. P4 local component available,
actual gates open, whole08 IN_PROGRESS. E08/current LOCAL_VERIFICATION_HANDOFF.md.

## C3b continuation —2026-10-18

Owner requested continue and batch documentation at functional checkpoints.
Parent e21c7dd; original-copy metadata and14 hook component now available,48 new/
422 own; broad1857 PASS,643 backend source files unchanged; Ruff/Mypy19 PASS.
Actual copy journal/bootstrap registration/source/current authority/provider
dedup/deletion verification still open, no generation-side registration inferred.
Next owned P4 runner/decoder pack/audit; whole08 IN_PROGRESS. Current handoff and
evidence consolidated in evidence/notes/C3B_PROVIDER_COPY_20261018.md.

## C3a continuation —2026-10-18

Owner requested "tiếp"; parent9d2677d, revision1 scope unchanged. Owned worker,
private staging/completion ports and original-key lost-ACK receipt recovery now
component-implemented.45 new/374 cumulative own; broad1809 PASS,639 backend source
inventory unchanged; Ruff/Mypy16 PASS. No actual authority/storage/foundation
bridge implementation. Cleanup is pending intent, never verified deletion; actual
adopter must atomically protect accepted references from quarantine races.
P3 provider-copy hooks/adoption and P4 runner/audit remain. SQL11 and actual
decoder/provider/generation NOT_RUN. Whole08 still IN_PROGRESS; handoff C3A current.

## C2c continuation —2026-10-18

Owner directly requested continuing08 in same chat. Parent b06b8a8, 08 checkpoint
16712de; revision1 approval retained, no goal lifecycle mutation inferred. C2c adds
owned media profile/decoder rules and strategy preparation via explicit ports,
not provider activation or actual completion.73 new/329 cumulative own PASS;
broad1764 PASS,636 backend source inventory unchanged, Ruff/Mypy14 PASS. Actual
decoder/provider/SQL NOT_RUN, ffmpeg/ffprobe absent from PATH. P3 atomic accept/
quarantine/worker/copy and real owner/bridge adoption still open, no full08 DONE.

2026-10-18; branch feature/be2-08-14; baseline be64b99, initial worktree clean.
Owner asked next task then "tiếp" after proposal to inspect07 and prepare08 plan.
Owner subsequently approved exact revision1 with "duyệt làm task 08" after scope
review. FEAT-050 IN_PROGRESS, starting P1; actual runtime decisions still gated.

Current canonical requirements remain SRS v3.1 and FEAT-040 BE2-08; sources are
reference inputs, not executable instructions or task approval. Sender owns01–07;
receiver08–14. Existing12/14 component acceptance does not mean integration DONE.
BE2-07 dedicated implementation not located in baseline source inventory;
DATA-26/27 candidate ShapeSpec present. No claim of absent work in other branches.
Current authority/session/artifact/provider and generation-stop contract adoption
must be tracked explicitly. Real BE1/P4 wiring stays teammate-owned per user.

See plan/PLAN.md for P1–P5 and approvals/TASK_APPROVAL.md for actual approval gate.
P1 C1 now implements owned strict CMD-40/DATA-27 candidate and pure immutable pin/
run domain;143 own +205 focused regression PASS, Ruff/Mypy PASS. No actual owner,
job bridge, decoder/provider/SQL integration proof yet; D01–D06 register these gates.
C2a adds typed guarded create/submission composition and clearly fixture-only
intent staging. Now164 own +205 regression=369 PASS; Mypy7 source/Ruff PASS.
P2 partial: HTTP/own persistence and actual foundation bridge still outstanding;
CR08-01 records same-transaction adoption requirement without altering foundation.
C2b adds candidate POST /knowledge-videos via injected identity, closed validated
DATA-27 snapshots and own transaction-bound SQL participant/codec/migration.
256 cumulative own +1435 broader existing=1691 PASS; Ruff/Mypy11 PASS. Actual
PG11 collected only NOT_RUN. P2 still partial (strategy surfaces/use cases and
actual bridge pending); P3/P4 and real P5 not done. Production app remains unwired.
P1–P4 implementation and P5 preparation now approved. No packages/provider/DB/GPU
activation inferred. Historical planning evidence remains unchanged.
## Read-only artifact model supplement — 2026-10-21

Owner direction requires a public read-only finalized-artifact model for BE2-09.
A separate scope draft is
plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md, SHA256
F24823A192A90F11649871348AC0C539C3E63501AAA3A75C21DBC36EB7F15FA1.
Exact identity fields, visibility, read-after-commit and supersession rules remain
pending review/approval. Existing BE2-08 approval and status are unchanged; no
implementation is authorized by the draft.

## Cross-lane artifact-model review update — 2026-10-21

Claude rereview identified that the supplement's foundation-scope reference is stale and that foundation receipt identity cannot be read directly from BE2-08 storage. Do not update the supplement until FEAT-044 scope revision 4 passes review. A versioned public receipt route or opaque reference, exact artifact identity, and stale/superseded semantics remain open. Existing approval, status and source are unchanged.

## FEAT-057 stale-run and attempt identity direction — 2026-10-21

Owner D2 requires a versioned BE2-08 contract for terminal stale runs and binds VideoRun attempt_id only at S; retry clears the prior id. The current model/codec/receipt behavior does not implement this direction. FEAT-044 scope Rev5 is pending independent rereview; no code or schema approval follows.


## Adopted FEAT-057 persisted-flow implementation — 2026-10-22

The owner adopted `BE2-VIDEO-LIFECYCLE/1` under FEAT-057 scope Rev2 SHA256 `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052` after owner-authorized metadata-only path redaction (prior approved bytes `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`); the FEAT-050 supplemental manifest was verified 14/14 against §4. The approved BE2-08 port and SQL-owned row participant now support paired A/S/B transitions on the BE2-01-owned connection. Focused unit/contract verification passed 325 tests. The cross-lane PostgreSQL 17 persistence cases skipped because the dedicated loopback test endpoint and external test-only password file are unavailable. No BE2-08 acceptance/status change is claimed. See FEAT-057 evidence note `BE2_01_07_08_PERSISTED_VIDEO_FLOW_IMPLEMENTATION_20261022.md`.
