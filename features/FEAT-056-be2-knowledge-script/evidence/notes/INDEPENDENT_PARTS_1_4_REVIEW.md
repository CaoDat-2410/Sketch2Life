# Independent review — parts 1–4

Reviewer: `plan_audit`, an independent read-only source reviewer. Implementation author:
`domain_author`. Approved plan revision 1 SHA256
`6de3ed6de3ef6008128d064ae28d3bf2b5fe78f91686afaa28eb63b4231aab36`.
Review authority is the direct owner execution instruction recorded in TASK_APPROVAL.
This review neither accepts the component nor closes deferred runtime/integration gates.

## A — mini-plan review, 2026-10-19

Read actual `PARTS_1_4.md`, approved plan, source audit/review, harness and source contracts.
Verdict: **PLAN_REVIEW_PASS** for parts 1–4. No concrete P1/P2 design finding.

- Part 1: immutable enriched basis/audience/contributor/imagined values and strict ref-only
  commands preserve the trusted boundary. Generic paths must call child consent zero times.
  Integrated current/disclosure guards remain to be proved in parts 5/7.
- Part 2: catalog lookup validates exact source and claim pins, review/recall/topic/age;
  Teacher attestation remains explicitly accountable under the named OD03 fixture policy.
  Public mutable publication paths remain to be proved in parts 6/5.
- Part 3: exact projections close KB-PR01; refs and text must not become independent inputs.
  NFC/casefold literal leakage checks are a heuristic, without semantic truth claims.
- Part 4: own canonical normalization must supplement the existing value-only helper;
  no-op returns a pure marker before correction allocation. Zero mutation effects require
  service/repository integration assertions later.

Existing source facts verified: `DownstreamMeaning` lacks organization/session/contributor
provenance; DATA26 ShapeSpec does not reject extras; the existing strict canonical helper
does not normalize mapping keys. Own implementation must preserve these explicit limits.

## C — actual implementation review checkpoints

### Part 1 initial review — NEEDS_FIX

Actual code and all current domain/contract assertions were read. Independent probe imports
the task worktree module; raw output is retained at local/reviewer-parts1-4/part1-initial-probe.log.

- **KB-C01 / P2** — `domain/knowledge_bundle.py:101`: confirmed basis stores only an
  analysis-like ref/revision and a boolean, without the exact Teacher confirmation reference.
  Trigger: construct the valid confirmed basis used by current tests without any confirmation
  identity; validation accepts it. Expected: trusted confirmed metadata includes the exact
  confirmation pin required by the approved plan, retained into historical canonical content
  and compared during current resolution. Minimal fix: add required confirmation metadata for
  confirmed meanings; preserve the Teacher-topic alternative. Regression: missing metadata
  rejects, exact pin survives projection and changed confirmation denies current eligibility.
- **KB-C02 / P2** — `domain/knowledge_bundle.py:134`: Teacher-topic basis permits nonempty
  child source snapshot refs while forbidding contributors and making zero consent calls.
  The independent probe constructs exactly this accepted combination. Expected: child-derived
  provenance cannot enter the generic branch without its contributors and eligibility checks.
  Minimal fix: reject source snapshots in generic Teacher topics. Regression: generic-with-child-
  snapshot fails while ordinary generic basis keeps zero consent calls.
- **KB-C03 / P2** — `application/ports/knowledge_bundle.py:21` and
  `domain/knowledge_bundle.py:189`: contributor eligibility callback carries no trusted
  organization/session scope. The same contributor/purpose/snapshot tuple cannot distinguish
  scoped consent facts; a fixture keyed only by that tuple could grant an unrelated session.
  Root independently raised this gap. Minimal fix: pass trusted scope with the contributor to
  the port; test same participant in different scope cannot borrow permission.

Integrated disclosure, sticky child-origin deletion, authorization and current-read behavior
remain deferred to their owning implementation parts; no PASS is inferred for those cases.

### Part 1 re-review — PASS_WITH_INTEGRATION_NOTES

Author added mandatory exact confirmation metadata to confirmed meanings and forbids all child
provenance in generic Teacher topics. Regressions explicitly reject both original probe inputs;
positive child fixture keeps `teacher-confirmation-1`. The fact-port consent method now carries
organization/session/contributor. The pure callback is deliberately a closure bound by the
application service; final integrated tests must prove the scoped lookup cannot borrow another
session's permission. KB-C01/02 are closed at the pure-rule boundary; KB-C03's port correction
is closed here with scoped fake/service execution retained as an integrated proof obligation.

Reviewer independently ran the two actual domain/contract files: **16 passed, 0 skipped**, exit 0.
Exact command, source/test SHA256 and EOL inventory are retained in
`local/reviewer-parts1-4/part1-rereview-receipt.json`, with JUnit and raw log beside it.
No remaining concrete P1/P2 in part 1's implemented scope. Current guard, sticky deletion and
role/disclosure behavior remain pending implementation in their owning parts.

### Part 2 initial review — NEEDS_FIX

- **KB-C04 / P2** — `domain/knowledge_bundle.py:327` (initial part 2 snapshot):
  `validate_claims` compared every Teacher-attested claim author with one current actor
  argument. Trigger: scoped Teacher B reads or edits story/sections while retaining Teacher
  A's historical attested claim. Expected: immutable A attribution survives B's operation;
  current source validation must not require reattribution. Minimal fix: derive/check server
  attribution when constructing newly edited claims, and validate existing immutable
  attestation structurally without comparing it to the current reader/editor. Regression:
  B can retain A's sourced attestation and its original author/reason remains unchanged.

The reviewer test attempt overlapped the author's immediate API fix: **9 failed, 18 passed**
because source had changed to five arguments while tests still passed six. This was an
in-flight source/test snapshot, not a new product finding or a passing review. Raw log,
JUnit, command and before/after hashes are preserved in `local/reviewer-parts1-4/part2-review*`.
A stable fixed checkpoint and rerun are required before C closes.

### Part 2 re-review — PASS_WITH_INTEGRATION_NOTES

`validate_claims` now validates exact source/catalog pins and structurally valid immutable
attestation, without a current actor argument. Newly constructed attestation still requires
server principal/reason. The regression keeps Teacher A's author and validates that sourced
claim without reattribution. Root retains the actual A-to-B service operation as an integrated
regression. KB-C04 is closed at this domain boundary.

Reviewer reran domain and contract tests on a stable before/after hash snapshot:
**27 passed, 0 skipped**, exit 0. Receipt/JUnit/log: `local/reviewer-parts1-4/part2-rereview*`.
No remaining concrete P1/P2 in part 2's implemented scope. Missing-source draft readiness,
provider/job counters and public catalog publication remain to be proved by parts 5/6/7.

### Part 3 independent review — PASS_WITH_INTEGRATION_NOTES

Read actual fact/story domain constructors, deterministic projection, strict command/response
DTOs and assertions. Commands reject arbitrary text and cross-kind refs; response validation
recomputes text from exact ordered refs, refusing unrelated prose under a valid claim ref.
Unknown/duplicate refs, NFC/casefold literal imagined leakage, removal of selected imagined
elements, changed-claim projection and total script bounds have concrete assertions.

Reviewer independently executed **32 passed, 0 skipped**, exit 0, stable source/test hashes.
Receipt/JUnit/log: `local/reviewer-parts1-4/part3-review*`. Independent local mutation probe
`probe_part3_mutation.py` removes only the response's exact section/flat text checks while
leaving reference existence checks. The actual KB-PR01 contract regression then fails with
`DID NOT RAISE`, proving this oracle catches the weakened ref-only rule; raw mutant and result
are local evidence. Production source was not changed by the probe.

No concrete P1/P2 found in part 3. The final version builder/service must always pass the full
trusted basis imagined set as forbidden literals, including selections removed by an edit.
The literal heuristic intentionally does not prove paraphrase detection or semantic truth.

### Part 4 initial review — NEEDS_FIX

- **KB-C05 / P2** — `domain/knowledge_bundle.py:614` with `version_document:575`:
  hidden typed provenance scope was neither canonicalized nor checked for consistency with
  the serialized version scope. Independent probe changes only the stored basis organization
  or audience session and `verify_version` accepts the original canonical bytes/hash.
  Expected: corrupted basis/audience scope fails closed before projection/eligibility.
  Minimal fix: validate all top-level/basis/audience scope invariants and bind or verify any
  omitted immutable fields used by projection. Regression: both hidden-scope mutants reject.
  Initial code/test bytes and hashes are retained in `local/reviewer-parts1-4/part4-initial-*`;
  actual accepted-mutant output is `part4-hidden-scope-probe.log`.

No source edit was made by the reviewer. Stable author fix and focused rerun are pending.

- **KB-C06 / P2** — `contracts/schemas/knowledge_bundles.py:283` (first full-basis
  snapshot checkpoint): standalone strict record validation still checked imagined leakage
  against selected elements only. Trigger: a full trusted basis contains the unselected
  imagined literal `Cats have wings.`; a Teacher-attested claim and its derived fact text
  use that exact literal. The record validates as generation-ready, although the domain
  producer correctly rejects it. Expected: candidate record/export validation preserves the
  same full-basis structural protection. Author independently identified the same issue.
  Minimal fix: validate the complete snapshot with domain metadata rules and check claim
  literals against all snapshot imagined elements. Regression: this crafted strict record
  rejects after selection removal; generic snapshot cannot hide child imagined provenance.
  Probe output: `local/reviewer-parts1-4/part4-record-basis-literal-probe.log`.

### Part 4 re-review — PASS_WITH_INTEGRATION_NOTES

KB-C05 is closed: version verification rebuilds through the pure constructor, checks coherent
version/basis/audience scope, enforces historical confirmed/applicable invariants and hashes a
full immutable basis snapshot. Tests reject both hidden-scope mutants, a changed applicability
flag, removal of an unselected protected imagined item and direct child-to-generic downgrade.
The full snapshot is checked against record provenance at the strict contract boundary.

KB-C06 is closed: strict snapshot DTO applies the domain metadata rules; record validation
checks factual literal leakage against the complete trusted imagined set. Regressions reject
the original attested-literal case, generic hidden imagined provenance and duplicate full-basis
imagined references. The producer continues to reject these cases before persistence.

Reviewer independently reran the stable final own domain/contract snapshot: **55 passed,
0 skipped**, exit 0. All five reviewed files are UTF-8 LF; before/after SHA256 are identical.
Exact command, JUnit, raw log and hashes: `local/reviewer-parts1-4/part4-rereview*`.
No concrete known P1/P2 remains in parts 1–4. All six findings KB-C01–06 are closed in this
implemented scope; no P3 finding was opened.

Integration proof obligations remain explicit: scoped consent/disclosure and Teacher role
checks, current full-basis/source/policy/audience validity, accepted receipt behavior, zero-effect
no-op, atomic corrections/receipts/events, no mutable alias publication, A-to-B historical
attestation, no-provider counters and exact current resolver behavior. Pure static record/export
conversion does not itself authorize current use. Real enriched producer/BE1/catalog adapters,
semantic source quality, durable storage, HTTP and consumer held fences remain deferred gates.

Final reviewed source SHA256:

| File | SHA256 |
|---|---|
| domain/knowledge_bundle.py | eee795b2954c510c0629b6431d91772bf7f64d96ec64b1e35edf5170cb6cd323 |
| contracts/schemas/knowledge_bundles.py | 34fccc9034a578ce68eadc0ae534ac6ed850097c8f96163cc88f3a96dae88c94 |
| application/ports/knowledge_bundle.py | 4f2c0985438de388e03b62e5f9b96cdff1bb8166700c88de1c0b5dc552499978 |
| tests/unit/test_knowledge_bundle_domain.py | 69ef8701a23f423c7853a86c6c84d9f7c5fedb9c90e38aa76f4ccb7d039ca8e4 |
| tests/contract/test_knowledge_bundles.py | 1a7566eafd2e71c12885354f67fa096633d60f3442f6e64ebfc944272a77d137 |

| Part | Source/assertions reviewed | Verdict | Open findings |
|---|---|---|---|
| 1 | Domain, strict create DTO, fact ports, 16 executed tests | PASS_WITH_INTEGRATION_NOTES | No P1/P2; integrated proof obligations retained |
| 2 | Exact source/catalog/claim rules, 27 executed tests | PASS_WITH_INTEGRATION_NOTES | No P1/P2; integrated proof obligations retained |
| 3 | Actual projection/domain/DTOs, 32 tests and independent mutation probe | PASS_WITH_INTEGRATION_NOTES | No P1/P2; full-basis binding pending builder/service |
| 4 | Actual versions/canonical/document/DTOs, 55 executed tests | PASS_WITH_INTEGRATION_NOTES | No P1/P2; integrated proof obligations retained |

Reviewed hashes and actual focused command receipts will be appended at each checkpoint.
