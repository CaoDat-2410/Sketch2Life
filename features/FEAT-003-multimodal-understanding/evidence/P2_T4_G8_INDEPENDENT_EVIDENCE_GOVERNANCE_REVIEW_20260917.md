# P2-T4 G8 Independent Evidence and Governance Review

Evidence ID: EV-003-T4-G8-01  
Feature: FEAT-003 Multimodal understanding  
Task: P2-T4  
Gate: G8  
Review date: 2026-09-17  
Review performer/session: Codex-G8-Independent-Audit-20260917 (fresh audit session)  
Designated independent reviewer: Project Owner / Person 2  
G7 author/reviewer: Codex under direct Project Owner authorization  
Authorized output: `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G8_INDEPENDENT_EVIDENCE_GOVERNANCE_REVIEW_20260917.md`

Final disposition: **G8: PASS — no new G8 defect**

This record is the formal independent G8 evidence/governance audit. It is separate from the G7
evidence-package correctness and scope review. G7 conclusions were treated as non-authoritative
inputs; the identities, topology, findings, and validator observations below were derived again
from the source artifacts and Git objects.

## 1. Independence, pre-G8 state, and exact scope

The G8 audit was performed in a fresh audit session, distinct from the G7 package-authoring
session. The G7 author/reviewer is recorded as Codex under direct Project Owner authorization. The
G8 reviewer role is designated to Project Owner / Person 2, and the execution record identifies
the fresh G8 audit session separately. No G7 result was copied as the G8 result.

The candidate and direct parent are:

- Candidate: `21249dc696c8ea3d958e78394ed69b8ac9f9505a`
- Direct parent: `dc107cd45a21ccb47031a58cb7c782084624bff4`

The exact non-ignored status captured immediately before this G8 record was created was:

```text
## plan/person-2-multimodal-fusion-conflict-detection...origin/plan/person-2-multimodal-fusion-conflict-detection
?? features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_CLOSEOUT_EVIDENCE.json
?? features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_EVIDENCE_REVIEW_20260916.md
```

Pre-G8 checks:

- `HEAD` resolved to the candidate and `HEAD^` resolved to the stated parent.
- `git diff --name-status` was empty.
- `git diff --cached --name-status` was empty.
- The two G7 artifacts were the only non-ignored additions.
- The authorized G8 path was absent and not ignored before creation.
- The retired `evidence/notes/` alternate path was absent and remained ignored.
- No tracked or staged modification existed before creation.

The only filesystem change made by this audit was creation of this one exact authorized Markdown
path. No G7 artifact, code, fixture, governance record, plan, freeze/package artifact, or other
path was edited.

## 2. G7 artifact preflight

Both existing G7 artifacts were read as exact working-tree bytes. Their raw SHA-256 values and Git
blob identities were independently recomputed. Because the files were untracked additions at the
pre-G8 baseline, the blob identities below are content identities computed with
`git hash-object --no-filters`, not commit-tree identities.

| G7 artifact path | Raw-file SHA-256 | Git blob ID | Bytes |
|---|---|---|---:|
| `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_CLOSEOUT_EVIDENCE.json` | `5b5e26753f5b4489cb559f06fc645884ca8e0af233cd563d791a56ad2ca5e40d` | `dfad83aac7a5c53bf5bab60239500f68f32e09be` | 13407 |
| `features/FEAT-003-multimodal-understanding/evidence/P2_T4_G7_EVIDENCE_REVIEW_20260916.md` | `f204dc33ad0d73a26db4596f8c9f657c4dbbf71a9fa911ca34a4a6007071f824` | `d906827e466f357c74af0cbaf6f58eb96eaf54fa` | 11731 |

The JSON parses as valid UTF-8 JSON with 19 top-level keys. Its candidate, parent, G6
`PASS_WITH_FINDINGS`, G7 `PASS`, G8 `NOT STARTED`, and G9 `NOT STARTED` fields were checked
directly. The paired Markdown carries the exact JSON raw SHA-256 as its final-evidence identity
and separately records `g7_package_review: PASS`, `g8_state: NOT STARTED`, and `g9_state: NOT
STARTED`.

The G7 package conclusions are not used as authority for this G8 disposition. The G7 artifacts
were only inputs whose content and identities were independently checked.

## 3. Candidate topology and seven-file bindings

The direct Git diff from the stated parent to the candidate contains exactly seven `M` paths and
no other path. Every candidate raw-file value below was computed from the exact bytes returned by
`git cat-file blob 21249dc696c8ea3d958e78394ed69b8ac9f9505a:<path>`, then compared with the
recorded binding.

| Status | Repository path | Raw-file SHA-256 | Git blob ID | Bytes |
|---|---|---|---|---:|
| M | `backend/src/sketch2life/application/services/p2_t4_fusion.py` | `6daa1b1eb49b665251e0e708454afc1449479437afe058effcfe22adf34ca823` | `0fd5d131f35c70e5b00139474888ded1570f9c8f` | 30602 |
| M | `backend/src/sketch2life/contracts/schemas/p2_t4_fusion.py` | `71d2ea0598f7667cb7dcbdcbc929d9d01a8475f47e3e1665168e7b2efd47513a` | `9ef7d2c60c0388c47516c623e395e7b573032ae6` | 29342 |
| M | `backend/tests/contract/test_p2_t4_contract.py` | `46156b4576dfb9f4f9c500ee0d6fb110ba593627dddec9f1b72f0e9972fe7759` | `651b92ac9a3d2af1ede69a5fab4c5323c36d7419` | 42821 |
| M | `backend/tests/unit/test_p2_t4_fusion.py` | `423e722a4e2f4f8c0f19cdee3275bf469e74b8afbeeaef4dcc14466e935a3097` | `37c31d9b1a8f6728657fa39893bcc265c35a6965` | 46535 |
| M | `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/cases-v1.json` | `f9a1b3bfe96f3234d01d76bf93b07aca6c921935d8802c3b6ecbaf151e14973e` | `60a852bfff1c488d1d213872e98c1b44eee338c6` | 25575 |
| M | `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/expected-v1.json` | `04604f1bcc5df0a698f646cfb284428c57576ed881ca30d62b66e4199e90447c` | `01d07242e222d00bd8fd4b70ecc053ec88f4b88c` | 90662 |
| M | `features/FEAT-003-multimodal-understanding/fixtures/p2-t4-fusion-v1/manifest-v1.json` | `ab60f306ca664391a7d94fe101d9305a6e626a0e58fd8e0e910839e666fd7ccc` | `4380e498e474eab27c7d654d4383c602568d3216` | 19928 |

The independently derived path set equals the seven recorded paths exactly. No code, test, or
fixture path outside this set is part of the candidate topology.

## 4. Dependency and lock bindings

| Repository path | Raw-file SHA-256 | Git blob ID |
|---|---|---|
| `backend/pyproject.toml` | `9ca3a54905d11fdb7f30a84356d23741f256b2115b254bcc9fba4efacdf17df6` | `8f8a344f505be839b9bd0bd0d640fa0d18cf6b33` |
| `pnpm-lock.yaml` | `b406b4c36c1e5304cf0c43b175c426d50aa3b43dc9a2bb81be357ea2b80b1665` | `20b0ecdd8247a2fcef8efd5d4b028082750635c4` |

Both values were recomputed from candidate Git objects and match the recorded dependency-lock
bindings.

## 5. Immutable freeze and package identity review

Each row contains the complete five-field identity tuple: repository path, source commit,
corrected normalized SHA-256, raw-file SHA-256, and Git blob ID. Corrected normalization was
recomputed from the exact source-commit bytes using the accepted erratum algorithm: CRLF and lone
CR to LF, exact full-line binding-table header match, removal through the first following blank
line, exact full-line revision-history heading match, removal through end of file, and SHA-256 of
the remaining UTF-8 bytes.

| Artifact | Repository path | Source commit | Corrected normalized SHA-256 | Raw-file SHA-256 | Git blob ID |
|---|---|---|---|---|---|
| Freeze revision 11 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_DRAFT.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `2b920e34f779ccbeabfec91e44858957b4f032dd6583879403b0fb748e367050` | `9521cb1482a10cefd235ea9596882d210912897289c182205aa93ee5a6685197` | `87227e5be0a58db88ac9f91ee7ddbdfa9bf4b05f` |
| Freeze revision 12 | `features/FEAT-003-multimodal-understanding/plan/P2_T4_CONTRACT_FREEZE_REVISION_12.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `103695e5e1c49d9f9b1cc85fd5286f42980580f338578db799febdeedb310ee5` | `b9606292e00b1b956ec38e141eb27f868bad2835f8ea5e8d20693a18acd2fa20` | `1e7e487362efec02b3b5f3bbf9dd4c64eabaa0d9` |
| Package revision 15 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260913.md` | `18d0c33d35431ca96a76692a68c6b992098699e7` | `7c76208d2ab3c98f9681fce67641049a93b21d2f0c2e9c843de1cac9e4d70b96` | `255034c587e89f8b72122c7377566684dd7a718257555c7fa92175a444255681` | `a4ade521f288c0d07c8c9cfdb1f6bbe6b41fa839` |
| Package revision 16 | `features/FEAT-003-multimodal-understanding/evidence/notes/P2_T4_IMPLEMENTATION_APPROVAL_PACKAGE_REVISION_16.md` | `5b6501b2d8b809f9dd4caf77b5c5d51d2e1e9cf2` | `75cd5d69e6896d7fae10d3771a90019003e0644fff1138161b7ac330e840b270` | `8ce46b5f762b27b556030d85666ccb6827a1fdbaeb56312dc8490d6e214a75ce` | `8784e84a537260668e81c6c889aadc8688086857` |

All four source documents remain `HOLD - NOT APPROVED`. The corrected identities are evidence
bindings verified here; this record does not grant a successor-freeze decision or implementation
approval.

## 6. Digest-binding erratum identity

The erratum has the required four-field identity only. No normalized self-digest was computed,
recorded, or implied.

| Repository path | Reviewed raw-file SHA-256 | Reviewed Git blob ID | Governance checkpoint commit containing that reviewed blob |
|---|---|---|---|
| `features/FEAT-003-multimodal-understanding/plan/P2_T4_DIGEST_BINDING_ERRATUM_20260915.md` | `8975d94b0d9be8e78935b66e1e851493c1cff5b2f1b83cdf49acfe7f9929276e` | `4b7ed999fed45e176d57c395e63fe62e8f12accc` | `c84a92990adac62477c076e6f660da3bef319175` |

The checkpoint source still states `READY FOR INDEPENDENT ERRATUM REVIEW — NOT OWNER REAPPROVED`
and renewed owner binding approval is `NOT GRANTED`. The four-field identity and boundary are
consistent with the erratum source.

## 7. G6 disposition and complete finding inventory

The G6 source report was read directly and was not rerun or rewritten by G8. Its recorded
disposition remains `G6: PASS_WITH_FINDINGS` for this exact candidate/parent pair. The G6 result
counts independently confirmed from that source are:

- Parent full backend pytest: 1,421 collected; 1,414 passed; 6 skipped; 1 failed.
- Candidate full backend pytest: 1,461 collected; 1,454 passed; 6 skipped; 1 failed.
- Focused P2-T4 tests: 317 passed; 0 failed.
- The single shared failure is the repeated fake FEAT-018 execution determinism assertion; the
  differing field is `adapter_wall_clock_ms`, while the remaining 20 evidence fields match.

The complete four-finding inventory is preserved below. G8 does not reclassify any item.

| Finding ID | Classification | Status | Location/fingerprint | Scope and disposition |
|---|---|---|---|---|
| `FEAT-018-TIMING-001` | shared baseline finding | `NEEDS_SEPARATE_REMEDIATION` | `backend/tests/unit/test_feat018_live_lightning_execution.py::test_repeated_fake_execution_is_deterministic_and_does_not_add_an_outer_attempt`; repeated fake evidence differs in `adapter_wall_clock_ms`, with the other 20 fields matching | Outside the P2-T4 seven-file scope; requires a separate FEAT-018 task and owner approval |
| `MYPY-BASELINE-001` | inherited baseline finding | `UNCHANGED_FROM_PARENT` | `backend/src/sketch2life/application/services/learning_media_resolver.py:101 (arg-type)`; `backend/src/sketch2life/application/services/learning_media_fallback.py:82 (arg-type)`; `backend/src/sketch2life/application/services/learning_media_fallback.py:85 (arg-type)` | Outside the P2-T4 seven-file scope |
| `RUFF-BASELINE-001` | inherited baseline finding | `UNCHANGED_FROM_PARENT` | `backend/src/sketch2life/contracts/schemas/learning_media.py:79 (E501)`; `backend/tests/unit/test_learning_media_scenario_matrix.py:1 (I001)`; `backend/tests/unit/test_learning_media_scenario_matrix.py:14 (E501)` | Outside the P2-T4 seven-file scope |
| `ARCHITECTURE-POLICY-B-BASELINE-001` | owner-approved Policy-B baseline | `UNCHANGED_FROM_PARENT` | application imports an outer layer: `backend/src/sketch2life/application/services/backend_ai_workflow.py` | Exact pre-existing baseline; not a P2-T4 regression |

The earlier semantic-catalog failures are not open findings; the G6 source records them as working
directory/data-layout issues resolved from the repository root with the documented PYTHONPATH.

## 8. Technical review pass

Result: **PASS**.

The independent technical audit verified:

- G7 JSON byte identity, valid JSON integrity, paired Markdown binding, candidate and parent
  identity, and the exact pre-G8 topology.
- Exactly seven candidate paths, with independently recomputed raw SHA-256 values, Git blob IDs,
  and byte counts matching every binding.
- Both dependency/lock bindings from candidate Git objects.
- All four complete freeze/package five-field tuples, including independently recomputed corrected
  normalized hashes using exact full-line matching.
- The erratum four-field identity, its checkpoint, and its explicit lack of a normalized
  self-digest.
- The candidate fixture bindings and their exact path set; no extra candidate path is hidden by the
  evidence package.
- Reproducible source and Git identity rules without JSON reserialization, newline substitution,
  or working-tree substitution for candidate files.

No technical identity mismatch, missing artifact, unexplained discrepancy, or reproducibility
defect was found.

## 9. Governance, scope, privacy, and status review pass

Result: **PASS**.

The independent governance audit verified:

- G6 remains `PASS_WITH_FINDINGS` and is separate from G7 `PASS` and the G8 result here.
- G8 was not treated as started before the pre-G8 baseline was captured; G9 remains `NOT STARTED`.
- The G7 package remains separate from the formal G8 audit, and G7 conclusions were not used as
  authority for the G8 disposition.
- The exact G8 output path is the only path created by this audit.
- No G7 artifact, code, fixture, governance record, plan, freeze/package artifact, FEAT-018
  artifact, or approval record was edited.
- No integration, runtime, provider/model, GPU, Lightning, network, migration, production, or
  live execution activity occurred.
- No commit, push, or PR occurred.
- The separately reported FEAT-018 timing finding remains open for separate remediation and is not
  silently skipped, normalized, or reclassified.
- The four source freeze/package artifacts retain `HOLD - NOT APPROVED`; no freeze, owner binding,
  or implementation authorization is implied here.
- Privacy/security scanning found no credentials, signing material, service-account content, real
  child data, raw media, raw transcript, or provider payload in the G8 record inputs.

## 10. Supplemental read-only validation

These checks were supplemental G8 observations only. They did not rerun or reclassify G6.

| Check | Result | Observation |
|---|---|---|
| `python tools/validate_harness.py` | `HARNESS_VALID` | Harness approval and frontend-asset gates enabled |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` | 1,045 publishable files scanned; environment, seed accounts, credentials/signing keys, and external reference documents excluded; absolute machine paths absent |
| `python tools/validate_skeleton.py` | `SKELETON_VALID` | Python/FastAPI backend, React Native frontend, Android-only target, Firebase Authentication-only, and declared workspace/AI topology accepted |
| `python tools/validate_architecture.py` | `ARCHITECTURE_INVALID` with one finding | The unchanged Policy-B baseline at `backend/src/sketch2life/application/services/backend_ai_workflow.py`; no new G8 finding and no candidate/parent delta |
| `git diff --check` | clean | No whitespace errors |

The architecture validator's non-zero result is reported truthfully. It is the same owner-approved
baseline recorded by G6, not a new G8 defect.

## 11. Discrepancies and limitations

- The two G7 artifacts were untracked at the pre-G8 baseline, so their Git blob IDs are content
  identities from `git hash-object --no-filters`; this is expected and was not treated as a
  candidate commit-tree binding.
- The architecture validator remains non-green because of the unchanged Policy-B baseline. This
  is inherited and outside the G8 defect taxonomy.
- G8 did not rerun the G6 full pytest, focused pytest, mypy, Ruff, or FEAT-018 test. The G6 source
  report and its complete finding inventory were independently checked, while supplemental G8
  checks were kept separate.
- The FEAT-018 timing finding still requires separate task scope and owner approval. This G8 record
  does not authorize its remediation.
- G9 remains `NOT STARTED`. This record does not authorize G9, integration, runtime, provider,
  model, GPU, Lightning, network, migration, production, commit, push, or PR work.

No limitation blocks the evidence/governance audit, and no new G8 finding was identified.

## 12. Final disposition

Technical review pass: **PASS**.  
Governance/scope/privacy review pass: **PASS**.  
New G8 findings: **none**.  
G6 disposition retained: **PASS_WITH_FINDINGS**.  
G9 status: **NOT STARTED**.

**G8: PASS — no new G8 defect**

