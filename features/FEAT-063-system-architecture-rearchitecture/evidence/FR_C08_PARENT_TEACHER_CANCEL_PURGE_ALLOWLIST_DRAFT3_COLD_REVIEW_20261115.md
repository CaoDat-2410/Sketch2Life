# FR-C-08 Allowlist Draft 3 Independent Cold Review

**Review date:** 2026-11-15  
**Verdict:** CHANGES REQUIRED ? 0 P1, 3 P2, 2 P3  
**Boundary:** Read-only plan review. This is not implementation approval or launch authorization.

## Review identity and scope

- Reviewer: fresh-context Codex reviewer `/root/fr_c08_allowlist_draft3_review`; no authoring-session context was inherited.
- The reviewer returned this review in chat and made no repository edits. This evidence file was prepared by the authoring session as a record of that response.
- Worktree: `.worktrees/m2-s2`; branch `feature/feat063-m2-s2`; HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51` ? MATCH.
- Reviewed target: `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT3_20261115.md` ? 62,813 bytes; SHA-256 `35DC6DD54D9170F670925D290B7788914EC383DF6EDCD0A797FBB98AAD279A00` ? MATCH.
- All 12 supplied strict byte-count/SHA-256 pins matched.

## Findings

### P2-01 ? Named-owner timing conflicts with the pinned specification

**Target:** Allowlist Draft 3 section 5, issue 4 (line 199).  
The allowlist correctly classifies named-person assignment as a launch-only governance gate and preserves technical ownership/contracts as implementation blockers. However, pinned Specification Draft 3 section 5.1 (line 60) requires named owners before an allowlist can be proposed, and section 9 (line 118) places them before implementation approval. Those gates conflict with D-208's before-launch requirement. Clarify that D-208 controls named-owner timing while retaining the technical blockers; the specification is unchanged by this review and any correction requires a separately authorized document task.

### P2-02 ? M2 coordination gate is weaker in the issue matrix

**Target:** Allowlist Draft 3 section 5, issue 9 (line 204).  
The row says not to rely on M2 as a ready baseline before reconciliation. D-208 requires the partial, dirty M2 baseline to be reconciled and pinned before any FR-C-08 implementation. Draft 3 states the stronger boundary elsewhere (lines 209 and 314), so make the issue row equally explicit and not conditional on reusing M2.

### P2-03 ? Audit implementation and completion gates are ambiguous

**Target:** Allowlist Draft 3 section 5, issue 10 (line 205).  
The row lists the audit-field allowlist, reader permissions, physical mapping, and 180/365-day map as unresolved, but describes required audit behavior as B-IMPLEMENTATION and the access/retention mapping as only a completion gate. It is unclear whether dependent audit implementation may proceed before those technical decisions. State which unresolved items block any dependent audit implementation and distinguish them from later completion evidence. Rev68 section 31.10(17) and D-208 leave these items OPEN-TECHNICAL; none may be inferred.

### P3-01 ? M2 test count is attributed to the wrong run

**Target:** Allowlist Draft 3 section 5, issue 9 (line 204) and its following paragraph (line 207).  
Draft 3 associates 81 passed with the final authorized combined invocation. The M2 report records 81 passed for an earlier owner-supplied run (lines 106-119). The later invocation is reported as exiting 1 at line 133; its captured final summary at lines 270-274 has no pass count. Separate the earlier count and do not assign an unstated count to the final run.

### P3-02 ? Lifecycle Plan Draft 3 repeats the unsupported Draft 1 characterization

**Target:** Allowlist Draft 3 section 2, Allowlist Draft 1 row (line 31).  
The allowlist accurately flags Specification Draft 3 section 9, but Lifecycle Plan Draft 3 section 7 (line 67) makes the same completed-run-only attribution. Draft 1 section 3's `parent_story_runs.py` E-path row says no completed-delete route was selected; it does not define DELETE eligibility. Extend the provenance note to cover the lifecycle plan or correct that companion document separately.

## Verified items

- Draft 3 correctly addresses the three Draft 2 review findings: named-person assignment is separated from technical ownership/contracts; the approval ledger acknowledges the separate FEAT-047 overlay and one-time S2 verification authorization and states neither approves FR-C-08; Draft 1 is described as a route-selection boundary with a section 3 row citation, not as defining completed-only DELETE eligibility.
- The lifecycle matrix matches Rev68/D-208: exactly 13 unfinished cancel states; explicit user-requested DELETE for `COMPLETED`, `FAILED`, and `ABANDONED`; no automatic purge of `FAILED` or `ABANDONED`; `DELETE_PENDING` until purge is verified; and `DELETED` only after verification.
- The target does not invent a route, schema, physical owner, retention mapping, or DDL. It remains proposed and does not approve or launch FR-C-08.

## Pins checked by reviewer

| Input | Bytes | SHA-256 |
|---|---:|---|
| Draft 3 | 62,813 | `35DC6DD54D9170F670925D290B7788914EC383DF6EDCD0A797FBB98AAD279A00` |
| Rev68 SRS | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| SRS authority | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| DECISIONS.md through D-208 | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| DATA_TABLE_REGISTER.md | 171,609 | `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` |
| Specification Draft 3 | 19,897 | `1D680D04D1B06ED827F0FFD71A30D5E2C2AFC09828158997276D1F8424F37313` |
| Lifecycle Plan Draft 3 | 13,246 | `832D3653A38BAF8E3D82D75C319D7BA275B7628510074932DF726F459EB8A95E` |
| Allowlist Draft 1 | 44,643 | `82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800` |
| Allowlist Draft 2 | 56,894 | `6D0A79408446A4D72A098965CCC78E7ED9FE5E0DE8D065C0DC1BCA1B3B347E70` |
| Draft 2 cold review | 7,496 | `96361FA0AB97D7DB9E0E1CC5F328F5FB6704B8D0580F525676F732E0D9A3CB1D` |
| FEAT-063 approval ledger | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| M2 implementation report | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |

## Limitations

This was a static, read-only review. No tests, validators, backend/runtime, database/migration, Docker, network/provider, or Modal commands were run. No plan, source, approval, or prior evidence was changed by the reviewer. This review is not implementation approval or launch authorization.
