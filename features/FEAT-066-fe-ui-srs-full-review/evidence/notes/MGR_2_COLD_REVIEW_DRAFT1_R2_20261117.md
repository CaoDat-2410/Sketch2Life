# MGR-2 Draft 1 Independent Cold Review R2

## Verdict: ACCEPT WITH NOTES

The MGR-2 draft is bounded to contract planning, keeps implementation unapproved, and correctly leaves unresolved behavior open. I found no blocking mismatch in the requested capacity requirements when checked against the repository’s canonical SRS.

### Finding

- **P2 — Authority and citation traceability:** The plan records an owner-selected external SRS as a task-specific input at [the plan, line 11](D:/GitHub/Sketch2Life/.worktrees/manager-api/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MGR2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md:11) and [the evidence, line 30](D:/GitHub/Sketch2Life/.worktrees/manager-api/features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md:30), while also saying it does not replace repository authority. Repository rules identify in-repo v2.7-draft Rev60 as the sole current product SRS ([AGENTS.md, lines 7–9](D:/GitHub/Sketch2Life/.worktrees/manager-api/AGENTS.md:7); [SRS_AUTHORITY.md, lines 5–14](D:/GitHub/Sketch2Life/.worktrees/manager-api/docs/context/SRS_AUTHORITY.md:5)). The evidence’s SRS line references appear to follow the external document’s layout; for example, its FR-T-03 `:542` reference differs from Rev60’s FR-T-03 at line 522. Keep those references labeled as external task-history provenance and add canonical Rev60 references for current requirements. I did not access the external file or independently verify its hash or Rev69/Rev68 discrepancy.

The reviewed claims are supported by Rev60: Billing capacity ownership and a versioned entitlement boundary (§9.7, line 815); 10 base slots plus paid add-ons and downgrade suspensions (§23.1 and §23.4, lines 1832–34 and 1867–69); transaction-time admission and 201/full-capacity behavior (§21.2, line 1622; UC-06, lines 1433–35); idempotency and replay (§21.4, line 1670); and GRACE/RESTRICTED behavior (§23.3, lines 1857–59). The broader Manager permission resolver remains open (§7.3, line 521; §31.10, line 2726), as the draft states.

### Source review and open items

- **VERIFIED FROM SOURCE:** The BE route creates and commits a class without a Billing capacity check or idempotency handling; its request accepts only `display_name` (1–200 characters). The route prefix, school-admin assignment check, error schema, active-only class list, and static router composition match the draft’s source account. Static composition is not runtime evidence.
- **VERIFIED FROM SOURCE:** At the recorded FE baseline `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`, the adapter sends only `display_name` and `X-Request-ID`; the page shows the capacity lock with no create action, and the test source asserts the create service is not called. Test presence is not test execution. The FE baseline is distinct from the manager worktree’s FE files.
- **PROPOSAL / OPEN-TECHNICAL:** The versioned Billing decision, concurrency-safe final-slot admission, receipt/reservation, recovery, and cross-owner boundary are proposals; exact mechanisms remain unresolved.
- **OPEN-OWNER / NOT VERIFIED:** Public outcomes for stale or unavailable Billing, idempotency header/details, route-prefix mapping, final response/error envelope, and the broader permission resolver remain open. Generated OpenAPI, runtime behavior, and test results were not verified; no tests, builds, validators, or runtime commands were run.

### D-066-62 provenance

**VERIFIED FROM SOURCE:** `D-066-62` is present in working-tree `DECISIONS.md` lines 260–268 and corroborated by `MGR_1_OWNER_DISPOSITION_20261117.md` lines 14–18. It is absent from pinned HEAD `1c9148e88600a101887e477541c4c4893ba1c7df` (blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50`, 34,226 bytes). The corrected evidence at [line 26](D:/GitHub/Sketch2Life/.worktrees/manager-api/features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_2_CLASS_CAPACITY_CONTRACT_DRAFT1_20261117.md:26) accurately describes it as a working-tree owner decision, not a committed baseline fact. The plan also correctly limits it to Teacher assignment candidates.

### Observed pins

- Branch/HEAD: `feature/feat066-manager-api-contracts` / `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Plan: 22,177 bytes; SHA-256 `900EA080B8E3E3C59FCF338D2249E1967FBEAEE87FF072422C1C534DB72A5A8E`.
- Evidence: 13,725 bytes; SHA-256 `52C502B48B63C8FB07F08F0AC0EE1CCE9FAC196CDE0D3440659A2D16E9236815`.
- Working-tree `DECISIONS.md`: 38,951 bytes; SHA-256 `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C`. Pinned HEAD blob: `ca0143cfd432bb70bfdf79e988228ef2066d9b50`, 34,226 bytes.
- R2 report destination was absent at preflight.

No input files were changed by the reviewer. This review grants no implementation or launch approval; MGR-2 remains DRAFT / NOT APPROVED / NOT LAUNCHED.
