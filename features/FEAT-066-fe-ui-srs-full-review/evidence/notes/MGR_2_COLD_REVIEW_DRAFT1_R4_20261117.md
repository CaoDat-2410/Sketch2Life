# Independent cold review — MGR-2 citation traceability

**Verdict: ACCEPT WITH NOTES**

**Findings by severity:** None. After correction, the artifacts distinguish Rev60 §9.6 line 791’s general idempotency-key requirement from the detailed scope and replay rules in §§21.1/21.4 and the mismatch error in §9.8. The route-group list at §9.6 lines 766–775 is not presented as the concrete key protocol. This is stated consistently in the plan at lines 37 and 66 and evidence at line 38.

The 11 external locator rows in evidence lines 36–46 map to canonical Rev60 locations. In particular, external FR-T-03 `(:542)` maps to Rev60 §7.3 FR-T-03 line 522, UC-06, and §21.2. No listed locator lacks a corresponding Rev60 source that would require an inferred requirement.

- **D-066-62:** Evidence line 26 correctly identifies it as present in working-tree `DECISIONS.md` lines 260–268 and absent at pinned HEAD in blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50` (34,226 bytes). I confirmed the working-tree content and absence at HEAD; MGR-1 disposition lines 14–18 corroborate it. Neither artifact claims it was in the committed baseline.
- **Authority and provenance:** The canonical v2.7-draft Rev60 SRS is unsigned and remains the working authority. The external SRS, its hash, and its reported Rev69/header-versus-Rev68-history discrepancy are explicitly historical and OPEN / NOT VERIFIED in plan line 11 and evidence line 30. I did not open or access the external file.
- **Open/not verified:** The artifacts retain the route-prefix mapping, broader permission resolver, exact key protocol and missing-key mapping, final class/error schemas, Billing unavailable/stale outcomes, and concurrency mechanism as OPEN or PROPOSED. Generated OpenAPI, tests, and runtime behavior are not claimed as verified. I made no owner-policy decision.
- **Source boundaries:** Spot checks support the static BE route, auth/error, composition, OpenAPI, and FE source claims. The FE source is pinned to `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`; its create action is unavailable, and test source asserts no create-service call. No test, build, validator, diff-check, OpenAPI generation, or runtime command was run.

**Observed pins:** Branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`; plan 24,013 bytes / SHA-256 `8D9780892575675DAC9FB7436D8A587FDDC61C0A9F2E5C27153969CAD1E1C055`; evidence 15,158 bytes / SHA-256 `762C89B81869D820DE9A04A1911724FA7CADA29BC1BEC833A3988447F8CAA6CA`. R2 matches 4,867 bytes / SHA-256 `67F1EE1C535404ECA0B150C102C0DB06B131419548AB12E57F7E77B3C69F969C`.

At reviewer preflight, the R3 path was absent. Before this report was saved, that path became occupied; it was left untouched and this report was saved as R4.

This review grants no implementation approval. MGR-2 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**.
