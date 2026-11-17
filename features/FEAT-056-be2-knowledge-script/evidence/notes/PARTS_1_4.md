# Parts 1–4 execution notes

Approval: revision 1 frozen SHA256 6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36; OD01–08 selected. This author owns only domain/knowledge_bundle.py, contracts/schemas/knowledge_bundles.py, application/ports/knowledge_bundle.py, domain/contract tests, and these notes.

## Part 1 A — mini-plan, before source

Implement immutable enriched basis, audience, contributor and imagined value objects. Validate exact scope/revision/confirmation/applicability and every child contributor's membership/purpose via typed callback/port. Generic topic has no contributor/consent lookup. DTO command union accepts references only and forbids attribution/scope/text overrides. Domain rejects malformed trusted metadata and duplicate/bounded facts. Pure helpers do not pretend to be a real DownstreamMeaning adapter. Tests cover generic/child positive, foreign scope/stale/unconfirmed/not applicable/missing provenance, mixed audience and per-contributor failures. Independent plan reviewer: plan_audit; root design review reports no concrete P1/P2. Check: focused pytest + Ruff/mypy on own files.

## Parts 2–4 A — staged mini-plans, reviewed before each source slice

2: immutable reviewed source/catalog claim pins; exact revision/hash, topic, every member age, review/recall state. Catalog text must match exactly. Teacher-attested source correction has server attribution/reason; named OD03 fixture policy permits readiness. Tests cover all bad pins/states and zero-claim draft; public catalog mutation review belongs coordinator parts6/5.

3: fact sections accept only ordered unique claim refs; story sections only exact trusted imagined refs. Text derives deterministically (separator newline) with literal NFC/casefold imagined leakage refusal. Strict projected response validates exact derived text at record boundary. Tests adversarial arbitrary text/unknown/duplicate refs, fact/story separation and changed claim projection; heuristic limit documented.

4: immutable version/head/correction construction. Canonical native JSON normalizes keys+values NFC, refuses collisions/floats/unsupported types, preserves array order, limits196608 bytes and script16000 chars. Exact bytes/hash verified; self hash/current readiness excluded. Create v1 and pure edit constructs v2/cumulative corrections, sticky child provenance; identical content returns None before correction/version allocation. Integration must prove no CAS/receipt/event. Test vectors/tamper/immutability/overflow and correction author/reason. No source change after closed part without rerun/review.

## Checkpoints

Part 1: A plan recorded; B pending; C pending.
Part 2: A draft recorded; B pending; C pending.
Part 3: A draft recorded; B pending; C pending.
Part 4: A draft recorded; B pending; C pending.

### Part 1 B checkpoint

Pure trusted values/guards and strict reference-only create command implemented. Focused15 tests PASS, no skips; source mypy strict PASS. Initial Ruff found13 line-length errors; formatter fixed all and Ruff retest PASS. Original pytest receipt parts1-domain.xml and retest parts1-domain-retest.xml/log retained locally. Current/historical integration guard and disclosure assertions remain explicitly pending parts5/7. C requested from independent plan_audit; next part awaits verdict.

### Part 1 C findings and fixes

Independent reviewer found P2 exact confirmation provenance absent and P2 generic snapshot provenance laundering. Added required confirmed-meaning confirmation_ref and generic provenance rejection. Added concrete regressions; focused16 tests PASS with zero skips, Ruff and strict source mypy PASS. Ports scope contributor authorization with trusted organization/session; service must bind this callback. Changed-confirmation-at-same-revision current disclosure regression remains integrated part5/7. Source/test bytes normalized UTF-8 LF before independent reviewed hashes. C re-review requested.

### Part 1 C closure / Part 2 B checkpoint

Independent C1 PASS_WITH_INTEGRATION_NOTES; reviewer pin/receipt at local/reviewer-parts1-4/part1-rereview-receipt.json. No known pure-boundary P1/P2 remain. Part2 A amended to exclude all client verification attribution; server infers exact catalog versus accountable Teacher attestation. Implemented immutable exact source/catalog/claim rules and strict bounded claim edits. Focused27 tests PASS, Ruff and strict source mypy PASS. Part2 C requested; public publication/race/current-read integration remains parts6/5/7.

### Part 2 C finding and fix checkpoint

Independent review identified historical Teacher attestation incorrectly tied to current caller. Removed current-author equality from trusted immutable claim validation; only newly constructed claim edits use server actor attribution. Historical author remains unchanged; integrated Teacher A→B edit assertion assigned root. Focused27 tests, Ruff, strict mypy PASS after fix. One transitional failed test call during API update retained parts2-review-fix.xml/log; fixed and retested parts2-review-fix-retest.xml/log. Reviewer transitional snapshot rerun retained independently. Own source/test paused during final C2 re-review.

### Part 2 C closure / Part 3 B checkpoint

Independent C2 PASS_WITH_INTEGRATION_NOTES (27 independently passed, stable before/after source hashes). Part3 implemented reference-only fact/story commands, deterministic ordered newline projection, exact response projection verification, literal NFC/casefold imagined leakage guard and bounded script. Focused32 tests PASS, Ruff and strict source mypy PASS; part3-domain.xml/log retained. C3 requested and own source/test paused. Literal guard does not detect every paraphrase; semantic model verification is outside scope.

### Part 3 C closure / Part 4 B checkpoint

Independent C3 PASS_WITH_INTEGRATION_NOTES;32 tests independently passed, exact projection mutant caught by actual KB-PR01 regression. Part4 implemented immutable versions/head/cumulative corrections and normalized native canonical bytes/hash; unsafe floats/nonfinite/tuple/bytes/object/key types, NFC collisions, malformed Unicode and huge integer serialization reject safely. Pure no-op returns None before correction/version allocation. Exact source pins, basis/audience/policy preservation, sticky child provenance and full-basis literal leakage enforce pure version invariants. Record/export bind all static fields to exact canonical bytes; source hash is separate from consumer digest. All16 actual DATA26 ShapeSpec fields represented (the task's17-field shorthand was reconciled to source). Focused53 tests PASS, Ruff + strict source mypy PASS. Receipts parts4-domain[-refined].xml/log retained. C4 requested; own sources paused during independent review. Atomic no-op/CAS/receipt/event proof and current export guards remain integrated scope.

### Part 4 C finding and fix checkpoint

Independent KB-C05 P2 proved hidden basis organization/audience session corruption could keep prior canonical bytes. Fixed verify_version to reconstruct all pure invariants and reject mismatched top/basis/audience scopes. Canonical basis_snapshot now binds all immutable trusted provenance including the full unselected imagined set; historical confirmation/applicability flags are invariant true, while current port decisions remain outside content hash. Added scope/applicability/full imagined tamper and direct origin downgrade regressions. Stable54 focused tests PASS, Ruff + strict source mypy PASS (parts4-review-fix.xml/log). C4 re-review requested; own source/test paused.

### Part 4 C closure

Independent re-review PASS_WITH_INTEGRATION_NOTES,55 tests independently passed. KB-C05 hidden scope/full basis and KB-C06 strict standalone full-basis literal/snapshot metadata closed. No known P1/P2 remain in reviewed pure/strict scope. Ports ownership handed to root for coordinated fixture extension; original five files otherwise frozen pending integration review. All parts1–4 A/B/C completed; downstream actual service/current/race assertions remain owned by root and are not claimed from these pure receipts.

Initial Ruff1/2 failures have copied_from_tool_transcript text segments in local logs with explicit metadata: these are text copies, not original stdout byte receipts; shell overall exit0 reflected final mypy, individual Ruff exits were not separately captured. Later Ruff checks pass.
