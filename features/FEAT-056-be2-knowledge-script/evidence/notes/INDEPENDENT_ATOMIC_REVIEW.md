# Independent review: atomicity, commands, export and final offline gate

Reviewer: independent Codex sub-agent `atomic_review`; source author: root agent.
Authority: approved revision 1, OD01–08; no owner component acceptance inferred.
Scope: parts 6 → 5 → 7 → 8. Reviewer owns this note and local reviewer probes only.

## Part 6 A: mini-plan review before implementation

Reviewed prompt, frozen approved plan §§5–10, project instructions/context/source register,
FEAT056 approval/context/decisions/progress, existing03 coordination and06 staged-store races.
No concrete P1/P2 in the proposed bounded single-process approach. This verdict closes design
review only; implementation assertions and integrated handler races remain NOT_RUN.

Recommended narrow boundary: coordinator `unit()`, consistent `read(callback)`, deferred
`publish(callback) -> bool`; repository `transaction()` plus a detached `snapshot()`; UoW reads
and stage methods for head/version/correction/receipt/audit/outbox. Every mutable guard fixture
uses the same coordinator publication path. No raw mutable dictionary/property leaks.

Required invariants and review oracles:

- Coordinator lock precedes store lock and spans final guard checks through state publication.
  Same-thread fact publication returns deferred and leaves the actual fact unchanged while the
  unit is open; it applies after both commit and rollback. Other-thread publication is proven
  blocked by synchronization events, then observed after release. Callback logs alone do not
  establish publication timing.
- Each stage failure compares the complete committed snapshot, including every collection.
  Retrying with the same operation key must commit once, without a stranded success receipt.
- Repository captures generation before staging; any accepted nested dirty commit changes it.
  Outer publication then raises conflict without replacing the inner head, receipt or event.
  Same-operation loser reloads the winning receipt only after rollback and current disclosure
  authorization. Inner success plus outer failure must leave one accepted result in storage.
- A snapshot or immutable return value must not mutate committed state. Guard fixture
  publications must use public named APIs, including source recall; bypass probes should fail
  on actual guard state, rather than merely record method calls.
- Deferred drain runs in `finally`, including failed units; failures do not strand the lock or
  discard later requested publications silently. This remains a fixture boundary, without a
  durable SQL fence or distributed-owner guarantee.

## Part 5 A: command mini-plan review prerequisites

Plan sequence and guard order are coherent. Read/disclosure authorization precedes receipt
replay; canonical semantic body excludes transient headers. Accepted receipt results survive
head advance, mutation-only pause and stale If-Match. Fresh keys still run current guards.
Explicit tests must distinguish replayed historical body from current generation eligibility.
No-op must leave snapshot, commit count and receipt collection unchanged.

Expected probes: same-key different body409; missing edit precondition428; wrong family/value
412; cross-principal/session safe denial; lost acknowledgement once-only state; accepted replay
denied after disclosure revoke; nested same-key winner must be reauthorized after queued revoke.
Actual implementation review remains pending.

## Part 7 A: export mini-plan review prerequisites

Resolve must verify the exact requested id/version/hash against stored canonical bytes and
current head, then recheck every current producer/guard pin. Withhold script on stale or denied
resolution, independently of outbox delivery. Export must preserve editorial/context/audience
revision separation and content-hash versus consumer-digest namespace. Consumer recording
fixture proves exact idempotent event application only; actual08 held fence remains deferred.
Actual implementation review remains pending.

## Part 8 A: final gate review prerequisites

Final42-row map must name executed nodes and concrete assertions, with truthful residuals.
Reviewer will inspect actual source, tests, JUnit and hash binding after implementation. Final
batch and reviewed hashes must bind the same code snapshot; a code change refreshes the batch.
Historical evidence/source01–06 must remain unchanged. Runtime/provider/adoption stay open.

## Concrete mini-plan re-review

Read root-authored mini-plans before corresponding source implementation:

| Part | Mini-plan SHA256 | A verdict |
|---|---|---|
| 6 | `31a520ce7ed4cd12d7ab44534db3deced8e45e3e883e86c90b50f1e6176439d3` | PLAN_REVIEW_PASS |
| 5 | `dbe36e261a0c3aa980e398bc09af9dc26742569755f82b791292e236214c9567` | PLAN_REVIEW_PASS |
| 7 | `24f1710ae36f0308453d56a6c30298db0daea7273830413e194a9c0805ffeade` | PLAN_REVIEW_PASS |
| 8 | `06f982a35f2757af7e9040148688ebd05ec6160858344163ae6805af392129a` | PLAN_REVIEW_PASS |

The written plans cover atomic stage rollback, deferred publication state assertions,
generation-protected inner winners, post-rollback replay disclosure, strict semantic body
matching, exact withholding independent of event delivery and the deferred08 fence boundary.
No concrete P1/P2 design finding remains. Parts6/5/7 B and C remain NOT_RUN until actual
implementation source and assertion review. Part8 source pin/collection/JUnit/hash binding,
actual42-node mapping and immutable history checks are coherent at design scope; final
readiness remains pending executed evidence. Baseline Pillow skips must be reported according
to observed final JUnit reasons/counts.

Drain exception review: continue all queued callbacks and retain an inspectable failure; a
successful unit followed by drain failure may behave as lost acknowledgement and must replay
its accepted receipt once. On unit failure plus drain failure, preserve or chain the original
failure so conflict recovery semantics remain explicit. Fixture setter input validation should
precede publication; a generic lock callback alone cannot roll back a partially mutating
callback. These are implementation review requirements, not findings against absent code.

Composition follow-up: a read-only opaque coordination token shared by fact and repository
ports is a bounded way to reject accidental mixed-coordinator service construction. Derive
the token from the actual coordinator and compare identity before operation; test mismatched
boundaries reject without mutation. This enforces the local fixture contract without adding
a generic coordination platform or implying distributed fencing. Actual source review pending.

Consumer candidate source independently read via local Git object
`2d5d9256bcbdb8c2465d720ab989a94fbb8ab6e7`,
`backend/src/sketch2life/domain/knowledge_video/model.py`; no import/merge performed. Actual
VideoPin digest material uses schema `BE2-08.VideoPin/0.1-candidate`, sorted source exact refs,
separate revisions and full profile/policy exact refs. Its canonical helper preserves Unicode
without NFC; producer candidate conformance must therefore remain limited to normalized native
JSON vectors and retain a distinct producer bundle hash. Part7 implementation review pending.

## Implementation review checkpoint

### Part6 initial source review — NEEDS_FIX

Read actual coordinator, repository and typed port changes. Initial repository SHA256
`9e851e7504f77ee8ba63fb8b916e8357ec276d5186edf5aa1f33be90ab431957`;
coordinator SHA256 `9c4e638b9a6538c5444eb111f8cb8ea34e547206d91dfc18cd4580afd1313daf`.

- **KB-A01 / P2** — `infrastructure/knowledge_bundle/fakes.py:157`: publishing
  `tx._state` directly retains a live write alias in a completed UoW. Independent probe
  commits headv1, leaves the context, then calls the public expired UoW `put_head(v2)`.
  Actual committed head becomes2 while repository commit count remains1, bypassing the
  coordinated transaction entirely. Expected: escaped/completed UoW cannot mutate committed
  storage. Minimal fix: detach the committed state from the UoW and preferably close UoW
  methods on every exit path. Regression: post-commit and post-rollback escaped writes leave
  the committed snapshot and count unchanged; active writes and nested winner behavior remain
  correct. Raw probe: `local/reviewer-atomic/probe_uow_escape.py` and
  `part6-uow-escape-initial.log`. No reviewer product-source edit was made.

Coordinator code correctly drains while still holding its reentrant lock, continues later
callbacks after failure and preserves the primary unit exception with a note. Full assertion
review, lock-window mutation oracle and repository re-review remain pending.

Part6 adapter mini-plan `PART6_ADAPTERS.md` independently reviewed: PLAN_REVIEW_PASS. Public
named setters, defensive copying before queueing, exact scoped contributor eligibility and
separate mutation/disclosure state are coherent. Actual adapters/source tests pending.

### Part6 re-review — PASS_WITH_INTEGRATION_NOTES

KB-A01 is closed: repository publishes a detached copy, closes the UoW before accepted hooks
and in `finally`, and every UoW read/write refuses a closed unit. Both commit/rollback escape
regressions assert unchanged full state and commit counts. Independent original probe now
raises KnowledgeStorageFailure and leaves headv1/one commit unchanged; fixed raw log retained.

Read all actual coordinator/repository/adapter sources, port changes and their assertions.
Reviewer independently ran the adapter and race modules: **25 passed, 0 skipped**, exit0,
with identical before/after source manifest. Source snapshot SHA256
`8fb8622000b2dd7bb5e98423e4cd5c359aa1303c5696522f09312c1e1135a593`.
Exact command/JUnit/log/import paths: `local/reviewer-atomic/part6-rereview/`.
The earlier independent adapter-only run also passed8 tests.

Assertions prove all seven staged-edit failure points roll back every collection, retry
commits once, inner accepted head/version/correction/receipt/event survive outer conflict,
snapshots/getters do not alias state, read-only units do not commit, nested same-thread queues
remain unapplied in actual state, other-thread publication reaches actual failed lock acquire,
and failed queued callbacks retain later publications/release the lock/preserve primary errors.
Every named fake guard setter is inventoried and checked against real values during both unit
commit and rollback. Exact scoped contributor and independent disclosure permissions execute.

Independent in-memory mutants leave product files untouched. The raw-publication mutant applies
facts immediately while returning False, so acknowledgement assertions pass; both real-state
window assertions then fail. Removing only the generation guard makes the real nested-winner
regression fail with DID NOT RAISE. Logs and probe source are in `local/reviewer-atomic/`.
These demonstrate effective race oracles rather than callback-order-only assertions.

No remaining concrete P1/P2 in implemented part6. Whole Rxx rows remain pending integrated
service proof for current guards, same-key recovery/replay, two editors, resolve/edit ordering
and queued revoke; this verdict does not claim distributed fencing or actual08 integration.

| Reviewed part6 file | SHA256 |
|---|---|
| application/ports/knowledge_bundle.py | `310c373ceb84cfcd30821bbd7fa909a9797cb76515e591c75fdaa7825795c0b5` |
| infrastructure/knowledge_bundle/coordination.py | `cbe5467f2463197307eef7f3ba0616392272ca032a7fdce1716752e318ac6c53` |
| infrastructure/knowledge_bundle/fakes.py | `edeb15a8e25027d8167fa5f9d75c23fb8160318cae037cdc8476ad41e3cd95fa` |
| infrastructure/knowledge_bundle/adapters.py | `cb0733ccdfd4e978e02b7eb5941688d9786c291649b0316394c63c5499ae2d13` |
| tests/unit/test_knowledge_bundle_races.py | `1a53bbbb38fd206c3243acc13be9b4e2518e26fdfdde149c9d7c27c493624d6c` |
| tests/unit/test_knowledge_bundle_adapters.py | `fb30ec44b14d0a0f93e1843a62093be65580386988c0f6bf5f825b46499e8b07` |

### Part5 harness/test mini-plan A

Independent atomic reviewer read `PART5_HARNESS_TESTS.md` before the harness/test source
slice. PLAN_REVIEW_PASS, no concrete P1/P2 design finding. Its scoped fixture composition,
actual consent counter, full-state atomic denials, historical A-to-B attestation and separate
future resolver/race proof are coherent. This review was performed by `atomic_review` after
the original plan reviewer became unavailable; it is not attributed to an unavailable agent.
Partial catalog misses must not silently produce ready content; accepted replay must check
current disclosure using the historical/sticky contributor lineage. Actual C5 remains pending.

### Part5 independent C review — PASS_WITH_OFFLINE_LIMITS

Read actual application service, harness, all33 service tests and expanded handler race
assertions. Reviewer independently ran all five own domain/contract/service/race/adapter
modules on the completed C5 snapshot: **175 passed, 0 skipped**, exit0, identical before/after
manifest. Snapshot SHA256
`5cb9c85e07eebc8ae0cd8825242a8176849b89dac1ea7eb9a81d874d2f1890f3`;
exact command/import paths/JUnit/log: `local/reviewer-atomic/part5-final-review/`.
Earlier intermediate104 tests also passed at the matching author's checkpoint; it is not
substituted for the completed175-test receipt.

No new concrete P1/P2 found. Service derives identity/attribution and exact semantic payload,
checks current disclosure before receipt matching, preserves accepted historical status/body
after head advance/pause/stale If-Match, and performs fresh current guards only on unseen keys.
Partial catalog misses become all-zero-claim drafts. Explicit bad-source edits leave full state
unchanged. No-op leaves commit/version/correction/receipt/audit/event state unchanged.

Executed integrated oracles cover15 actual guard families before a unit and queued during a
unit, six rollback/drain families, seven handler storage stages/retry, same/different-key nested
create/edit winners, queued disclosure revocation during nested recovery, lost acknowledgements
for both commands, actual two-editor contention and blocked other-thread source recall. Current
reads inside the commit window show the old script; reads after queued publication withhold it.
Four scoped consent negatives cannot borrow org/session/purpose/snapshot grants; a separately
wrong trusted purpose denies even with a positive consent grant. Historical Teacher A claims
survive Teacher B's real section edit. Client scope/attribution injection, all four role negatives
on create/edit/read, changed same-revision confirmation and sticky imagined removal execute.

Two independent in-memory handler mutants were caught by actual regressions: skipping replay
disclosure returns false success after nested queued revoke; applying fresh current guards to
accepted replay incorrectly fails after pause. Raw probe/logs: `local/reviewer-atomic/`.
Product files were unchanged by probes. Mixed repository/fact boundary construction has a
correct constructor rejection; its explicit negative assertion is retained for the final chain
test before part8. Exact consumer export/invalidation conformance remains part7; real authority,
storage, HTTP, semantic source quality and08 held fences remain unproved offline limits.

| Reviewed C5 file | SHA256 |
|---|---|
| application/services/knowledge_bundle.py | `e01a782d55fcd3dd4ba2020553ed3854384810ef094429443de2985b52a3e328` |
| infrastructure/knowledge_bundle/harness.py | `34e6f8fed3d4d14efe94ce49f725966ff4ce0b38939d156daaec76e66a026eca` |
| tests/unit/test_knowledge_bundle_service.py | `ab2953253b2fdca2a2857b1c5eab2f13ff95134363bce22dfc3d378c71a407c4` |
| tests/unit/test_knowledge_bundle_races.py | `119eb262adfe615c689e1b5cc60e6d267ab06544bd1ebc66d92f191737038839` |

### Part7 consumer/conformance mini-plan A

Read actual `PART7_CONSUMER.md` before its source slice. PLAN_REVIEW_PASS, no concrete P1/P2.
Explicit synthetic consumer-owned exact refs and reviewed-library strategy are appropriately
distinguished from the actual producer export and production adoption. Required independent
expected material/digest vectors and NFD difference preserve the namespace/canonical limits.
Actual C7 source/assertion review pending.

### Part7 independent C review — PASS_WITH_OFFLINE_LIMITS

Read the actual consumer projection/material helpers and all added adapter assertions, with
the pinned consumer08 source independently read earlier. Reviewer independently ran adapter
and service modules: **47 passed, 0 skipped**, exit0, stable before/after snapshot SHA256
`fdafbd3ef852bf3077220d556fc6d7d79d7279504c16555dc587ece294dde4f5`.
Exact command/JUnit/log/import paths: `local/reviewer-atomic/part7-review/`.

No concrete P1/P2 found. Actual producer v1 resolves before edit; v1 is withheld after v2
commit while the recording consumer has received no event. Original canonical bytes stay
unchanged. Current v2 export retains exact source/basis pins and separate revisions. Actual
transaction-getter byte/hash tampering withholds export without writes. Recording consumer
applies once, rejects conflicting reuse of event identity, preserves invalidation before late
registration and leaves other bundle/version/hash/org/session pins unaffected.

Candidate VideoPin material matches the actual pinned schema/strategy/refs/sorted-source
shape. Constant full material and known digest bind the producer fixture; normalized native
vectors have fixed expected hashes, and explicit NFD vectors prove consumer/producer Unicode
canonicalization differs. Drafts cannot be pinned. The corrected stable UTF-8 test text was
inspected; earlier in-flight mojibake failure is retained in author evidence, not counted PASS.
Synthetic profile/policy/library refs, current-resolution requirement and missing08 held fence
remain explicit. This fixture proves conformance/projection, not delivery or consumer adoption.

| Reviewed C7 file | SHA256 |
|---|---|
| infrastructure/knowledge_bundle/adapters.py | `521dfd642d2aed5c47a4e27904d2aabb672c0c4b3d2df1a58b0f6b8c8792b2ff` |
| tests/unit/test_knowledge_bundle_adapters.py | `918613ed17b834d65794c87e2be459b858f9005c1e01b9c3c29b554470f5c075` |

### Part8 examples mini-plan A

Read actual `PART8_EXAMPLES.md` before source. PLAN_REVIEW_PASS; no concrete P1/P2. Generate
from real service/harness only, compare two fresh producers plus parsed artifact JSON values,
and distinguish accepted historical ready receipts from current exact eligibility. Teacher
attestation accountability and synthetic consumer/held-fence limits must remain explicit.
Actual source/artifact/assertions and final42-map/JUnit/hash review remain pending.

### Part8 independent C review — PASS_WITH_OFFLINE_LIMITS

Independently re-read the post-fix producer, artifact and concrete assertions. The example
test now pins generic create `201`/not-replayed, Teacher edit `200`/not-replayed, and accepted
historical create replay `201`/replayed, in addition to the deterministic producer/artifact
JSON-value equality and representative export, event, no-op, provenance and denial behavior.
The P3 assertion gap is closed. Focused adapter+chain rerun: **23 passed, 0 failed, 0 skipped**,
exit0, Python3.12.10; exact local receipt/JUnit/log: `evidence/local/reviewer-independent-part8-rereview/`.
JUnit SHA256 `4600607d5fafd5f378dc53d0ca47f27ac60fcbceacd1b956a2eda3ffae7fc896`;
log SHA256 `ba234477ac90a17eea32d301da209f180d467c375c7cb1d314ce686a9078900b`.

No remaining concrete P1/P2/P3 found in the reviewed Part8 producer/examples scope. The
artifact explicitly limits Teacher attestation, synthetic fixtures, consumer projection and
the unproved 08 held fence/delivery. This review does not cover the final42 map or required
01–07 batch, which remain pending.

| Reviewed Part8 file | SHA256 |
|---|---|
| infrastructure/knowledge_bundle/examples.py | `6d7531d639582834b32e0df4837bb2907b7b88b16820f3cf66c37249d4af6164` |
| infrastructure/knowledge_bundle/adapters.py | `521dfd642d2aed5c47a4e27904d2aabb672c0c4b3d2df1a58b0f6b8c8792b2ff` |
| tests/unit/test_knowledge_bundle_adapters.py | `4bb71ca3fe1d6e62a3fc7eb3d65c5aa7b1a652f1962e6e23ffd2e6a5d0b2c9da` |
| tests/unit/test_knowledge_bundle_chain.py | `93cb617554dd298b841482f3fb51f5eef9301a1c48da85130094db66f6c40500` |
| artifacts/KNOWLEDGE_BUNDLE_EXAMPLES.json | `0f06aeace8bd0dd50e53096c2f0782a83001e47963c0383e180f117501b90f2c` |

### Final evidence runner sanity review

Read the feature-local runner source before execution. Worktree-root derivation, source path
insertion, subprocess PYTHONPATH/MYPYPATH, exact own-module import-path assertions, baseline572
plus own source/test/config manifest and new-directory-only output are coherent. No concrete
P1/P2 found in this tooling review. Suggested evidence refinements sent to author: per-command
UTC start/end and executable identity, final branch check, and finalize aggregate receipts even
after failed collection rather than returning before source-after/checks summaries. Collection
raw log and its individual exit receipt already survive a failed collection. Final review of
actual logs/JUnit/map remains pending.

### Final required offline batch independent C audit — PASS_WITH_OFFLINE_LIMITS

Independently audited the refreshed `final-offline-20261020-rerun1` receipts, approved
revision-1 plan, frozen batch profile, actual acceptance-map rows and raw JUnit XML. The map
contains the same 42 acceptance IDs in the approved plan's order; all rows are `PASS_OFFLINE`,
have concrete assertions and empty residuals. Its 279 exact mapped JUnit nodes all exist and
passed; no mapped node is skipped, and every `executed_nodes` entry normalizes to the row's
`final_junit_nodes`. I spot-checked high-risk producer, provenance, replay, guard-publication,
race, tamper and no-runtime claims against their concrete test nodes/source assertions.

Raw JUnit has 1,515 unique test identities: 1,512 passed, zero failures/errors and three
explicit Pillow-dependent live-app skips. The summary has the same 1,515 case identities and
counts. Those three skips remain NOT_RUN, and the excluded Pillow-importing V2 runtime module
is explicitly NOT_RUN. The profile points at this rerun and selects exactly 50 baseline plus
six required07 files (56 total); its selected-file hash and all mapped test files match.
All 11 recorded commands and validator receipts exit zero and their log hashes match. The
before/after manifests are identical, and all 595 manifest entries match the current files.
All 11 unique map evidence references exist. A scan of the four publishable metrics files
found no absolute machine paths or credential-like values.

Offline limits remain correctly stated: runtime execution and dependency installation are
false; component acceptance is `NOT_ACCEPTED`, the card is `IN_PROGRESS / NOT_DONE`, and no
live source/provider/database/HTTP/Lightning or actual08 held-fence execution is claimed.
This evidence establishes offline fixture/batch behavior only, not owner acceptance or
runtime adoption. No concrete P1/P2/P3 found in this final-map/JUnit/invariant audit.

| Final audit evidence | SHA256 |
|---|---|
| Approved `PLAN_REV1_APPROVED.md` | `6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36` |
| `ACCEPTANCE_MAP_BE207_20261020.json` | `98d9d9a582a9bb39987992a953d3821c19ce0ec4bdcfc166368ac10de3581466` |
| `BE207_FINAL_OFFLINE_CHECKS_20261020.json` | `c4382d693def6327b3adf09c85ee4b73bb05a37e849bba1bd6071a8f00b2bb3a` |
| Rerun1 `junit.xml` | `77b48bfd6858ec7aebfe8ccccccdb56a6389f9d5fae210909da65f7b16189701` |
| Rerun1 `source-before.json` and `source-after.json` (identical) | `7d204d1feddcd21082f422c6eab5188f9dafe461b035ca31484495f36afe0cf9` |
| Rerun1 `selected-files.json` | `daaba05409651d6883a522347904aeb383999d7eeae4a10add0d4914096be430` |
