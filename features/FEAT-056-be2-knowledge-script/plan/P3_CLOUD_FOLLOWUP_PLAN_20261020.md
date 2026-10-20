# BE2-07 cloud P3 follow-up plan

- Status: APPROVED / IN_PROGRESS.
- Authority: `../approvals/P3_CLOUD_FOLLOWUP_APPROVAL_20261020.md`.
- Starting published snapshot: `f0359c4fbb7c3f4a35dd3f2265559779a17951e9`.
- Input: user-pasted Claude cloud summary; session and raw-file provenance are recorded locally.
- Findings: P3-N1 invisible characters outside Cf; P3-N2 assert-based verifier under Python -O.
- Frozen revision 1 / OD01–08 and all earlier immutable approvals/reviews/metrics remain intact.

## A. Archive and reproduce

Preserve the user-supplied pasted summary separately from the actual cloud REVIEW.md. Obtain
the real REVIEW.md and OUTPUT_INDEX.json plus the 83 indexed output files, check paths, exact
hashes and report/source identity. Never manufacture missing raw files from the summary.
Keep `evidence/cloud-review/` until this prerequisite is satisfied. Save its published bytes
and provenance in ignored local evidence before any modification or eventual deletion.

Reproduce N1 using real service/domain/DTO paths and N2 with normal, -O and -OO interpreters.
Store assertion failures and commands in a new feature-local evidence directory. No installs.

## B. Small corrections and regression checks

N1: retain the existing comparison-only Cf normalization; additionally remove Unicode 15.0
Default_Ignorable_Code_Point ranges before NFKC and after normalization/casefold. This includes
CGJ, variation selectors and Hangul fillers, including their compatibility-normalized forms.
Do not discard ordinary combining marks: Vietnamese accents and token boundaries remain
meaningful. Preserve stored text and canonical serialization; no semantic or general-homoglyph
guarantee is added. Share Cc control validation between domain and DTO, allowing only LF/TAB.
Reject DEL/C1 rather than silently rewriting input.

The property source is the official Unicode 15.0 DerivedCoreProperties data, matching the
existing Python 3.12 unicodedata baseline:
https://www.unicode.org/Public/15.0.0/ucd/DerivedCoreProperties.txt
Only comparison policy is changed. Default-ignorable folding may conservatively equate emoji/
complex-script variants; the existing literal heuristic is not semantic truth verification.

Tests cover reported code points, CGJ between a base and Vietnamese combining accent, both
comparison directions, empty signatures, unrelated words/diacritics, original text/canonical
preservation, DEL/C1 rejection in domain/DTO, LF/TAB acceptance, and atomic real handler denial.

N2: make the existing assertion-dependent historical verifier fail closed before validation
whenever Python optimization disables assertions. Explicit exit must remain active under -O
and -OO; neither valid nor invalid pins may produce PORTABLE_EVIDENCE_VALID in those modes.
Normal mode still accepts the pinned historical copy and rejects a wrong commit/tampered bytes.
Preserve prior export provenance; describe/rebind only the verifier derivative. Since N1 changes
product bytes, the old product pins intentionally remain historical and are not silently rebased.

## C. Review, final local evidence and publication

Obtain independent review of the corrected source/tests/tooling; fix concrete regressions.
Run six task07 modules and the approved 56-module batch in the existing local venv, Ruff,
strict mypy and harness/architecture/skeleton/security/whitespace validators. Keep the three
Pillow live-app skips and excluded V2 server as NOT_RUN; no runtime/adoption is inferred.
Use new no-overwrite receipts/maps/handoff and exact source/tooling manifests. Preserve the
existing 42-ID acceptance coverage, distinguish product nodes from evidence-only gates, and
audit raw JUnit/receipt bindings before reporting review-ready.

Publish focused fix/evidence commits after required repository checks. If the cloud raw archive
is complete, remove only the exact reviewed cloud-review folder in a separate cleanup commit,
update current routing links to the immutable historical Git commit, and rerun the required
repository/evidence checks. Keep all historical commits/metrics/approvals unchanged. Never
delete ignored original evidence. If raw cloud files remain unavailable, finish independent
corrections and publication, report the pending archive/cleanup step and keep the folder.

## Acceptance

- N1 attacks fail through domain, DTO and real handler with no write/export; Vietnamese/control
  positive controls and original canonical serialization remain correct.
- N2 optimized execution exits nonzero without PASS; normal expected/wrong/tampered cases work.
- Fresh focused/full local checks and independent product/evidence reviews pass with honest limits.
- Old immutable records retain their exact hashes; new handoff stays NOT_ACCEPTED / NOT_DONE.
- Branch push is verified. Conditional cleanup happens only after full raw archive verification.
