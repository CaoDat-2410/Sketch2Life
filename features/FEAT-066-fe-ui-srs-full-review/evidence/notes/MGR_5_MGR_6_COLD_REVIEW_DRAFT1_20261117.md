# Independent cold review — MGR-5 and MGR-6 Draft 1

Review type: fresh-context, independent, read-only planning review. This report is not implementation approval, FE integration approval, or launch authorization.

## Preflight and reviewed pins

BE worktree: D:\GitHub\Sketch2Life\.worktrees\manager-api  
Branch/HEAD: feature/feat066-manager-api-contracts / 1c9148e88600a101887e477541c4c4893ba1c7df  
FE worktree: D:\GitHub\Sketch2Life\.worktrees\ui  
Branch/HEAD: codex/fe-ui-web-remediation / 297a28b1f406ab80e25d6e0aa5577e4b6f505ee2

All four Draft 1 byte counts and hashes matched the pins supplied to the reviewer. Canonical Rev60 also matched its recorded pin and SRS_AUTHORITY.md. The reviewer read both plan/evidence pairs in full and checked the relevant source directly.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| MGR-5 plan | 10,846 | 0174E6714379322E8904BEBD3BD0F18524105A871C20A1AF34EBF034FE3D5FBE |
| MGR-5 source evidence | 9,733 | B9424A154F8296661453BCD227334A35B4B6C4ACC1F17F102C90359E7627ED10 |
| MGR-6 plan | 13,110 | F6986B16836B98F9D82C811B4C82166F7551AA36DF5CCBC4D733F445E16E6D0B |
| MGR-6 source evidence | 11,157 | 3443AB0F9735E1D64FD5DA9F22E58CB3D11E0458F50F265802A2A847E2ADF237 |
| Canonical Rev60 SRS | 553,948 | 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B |

## MGR-5 — ACCEPT WITH NOTES

The plan/evidence pair correctly keeps Parent-profile consent and grants Parent-owned, and distinguishes a staff-created pending row from effective Parent consent. The owner brief asks whether a separate school-managed workflow is needed and identifies the policy inputs required before a write contract. D-066-62 is correctly treated as working-tree provenance, not pinned-HEAD content: it appears in current DECISIONS.md lines 260–268, is absent from the pinned-HEAD blob, and is corroborated by the MGR-1 owner disposition at lines 14–18.

### Findings

- **P2 — Clarify the write gate is a policy gate, not verified backend enforcement.** Plan Goal line 8 and the owner brief's “Safety boundary until decided” state Manager writes are unavailable. The source still declares record/revoke handlers at be1_registry.py:493–545 and 582–631; they accept assigned school_admin/teacher principals and are statically included by be1_runtime.py:19–24 and the router compositions. Runtime/deployed reachability was not checked. Keep the statement explicitly scoped to the product/FE gate; do not imply the existing BE routes are technically disabled.
- **P2 — Map consent-list pagination to Rev60.** The plan's route table at line 24 notes GET consent has no pagination. Rev60 §21.1 requires cursor pagination for list APIs, with default 25 and maximum 100. The current handler at be1_registry.py:548–579 has no pagination inputs. If this read route remains in scope, record the missing pagination as a source/SRS gap.
- **P3 — Cite the router prefix at its declaration.** The full path uses /api/be1/v1, declared in be1_registry.py:54. The composition evidence in plan line 30 establishes router inclusion but does not by itself establish the prefix; cite both when supporting the full path.

Other checked claims were supported by source: request DTO fields, pending/revoked persistence states, verified-adult and assignment checks, missing create-side class/child validation, static composition, catalog metadata, legacy projection, and the Manager FE's read-only caller. Static declarations/composition/catalog, test source, and runtime evidence remain distinct. The test source at test_be1_postgres_api.py:738–755 was not run.

## MGR-6 — CHANGES REQUIRED

### Findings

- **P1 — Correct two existing route paths in both artifacts.** MGR-6 plan lines 28–29 and evidence lines 23–24 place Manager grant listing/decision beneath /lessons/{lesson_id}/access-grants. The pinned router instead declares GET /api/lesson-library/v1/organizations/{organization_id}/access-grants, with optional lesson_id query filtering, at lesson_library.py:436–453; and POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision at lines 456–479. The static operation catalog and FE client use those org-level paths (openapi_contract.py:9509, 9575; backendApi.tsx:446–453). This is a material source-inventory error in a contract-planning artifact.
- **P2 — Separate SRS requirements from the Manager-specific contract proposal.** Evidence line 50 labels exact grant-version/hash review a “Required target from Rev60.” Rev60 §31.3 line 2536 requires exact version/hash pins through occurrence, plan revision, and StoryRun; lines 2547 and 2560 require School Manager review of Teacher content before PUBLIC. Those clauses do not specify a Manager review API or require the grant itself to carry a hash. The exact-version Manager read/binding is a reasonable contract proposal, but should be labeled as such rather than stated as a direct SRS requirement.
- **P2 — Record current superseded-grant behavior separately from the open policy outcome.** The plan leaves the superseded pending-grant outcome OPEN at line 50. Source service.py:1193–1220 checks grant state/revision and updates the version named by grant.version_id; it does not compare that version to the lesson's current version. FE ManagerScreens.tsx:70–72 and 247–265 blocks when the current version ID differs. State both source behaviors as static facts while retaining the product outcome as OPEN.
- **P2 — Define the proposed hash-binding mechanism.** Acceptance criterion 1 at plan line 72 says the hash is “from the grant,” but the current request/response and persistence carry version_id, not a grant hash (schemas/lesson_library.py:79–93, 172–186; tables.py:184–225). A future contract must explicitly propose either storing/binding the hash on the grant or resolving it through a version record whose immutability is enforced; neither mechanism is current verified behavior.
- **P2 — Record the list-limit mismatch.** The Manager grant-list handler defaults limit to 50 at lesson_library.py:442. Rev60 §21.1 specifies a default list page size of 25 and maximum 100. The plan notes cursor paging but not the default mismatch.

Other inspected claims were supported: current lesson detail follows current_version; no Manager GET-by-version route appears in the inspected router/catalog; grant DTO/table lack content/hash; decision uses grant version ID and revision; database-level content/hash immutability was not established; FE uses an ID-only guard and sends If-Match plus Idempotency-Key. The SRS does not settle the outcome for a pending grant whose source version is superseded. Static composition, static operation catalog, legacy projection, test source, and runtime remain distinct; no runtime behavior was verified.

## Provenance, limits, and disposition

- D-066-62 is verified in the current working-tree DECISIONS.md at lines 260–268 and absent from the DECISIONS blob at pinned HEAD. The MGR-1 disposition corroborates provenance; it does not make the decision committed. D-066-63 is MGR-2-specific and was not used as an MGR-5/MGR-6 policy basis.
- Not verified: deployed route reachability, external gateway/proxy prefix mapping, generated full OpenAPI output, runtime responses, test results, database immutability enforcement, and any owner decision on school-managed consent or superseded pending-grant policy.
- MGR-5 is reviewable with the non-blocking notes above, but its separate school-managed workflow decision remains OPEN. MGR-6 requires correction of its route inventory and resolution of the traceability findings before it is review-ready.
- No files were edited by the reviewer. No tests, builds, validators, OpenAPI generation, runtime, database, Docker, network/provider, or Modal commands were run. This review authorizes no implementation or launch.
