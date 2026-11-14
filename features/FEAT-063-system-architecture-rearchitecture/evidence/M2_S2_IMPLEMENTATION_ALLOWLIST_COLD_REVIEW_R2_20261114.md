# M2 S2 Implementation Allowlist Draft 1 — Independent Cold Review R2

**Review date:** 2026-11-14  
**Verdict:** READY WITH NOTES  
**Finding counts:** 0 P1, 0 P2, 1 P3

This review supersedes the initial cold-review report `M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_20261114.md` after `PROJECT_CONTEXT.md` and `SOURCE_REGISTER.md` were updated with the first review result and the allowlist E pins were refreshed. No implementation source changed.

## Current pinned inputs verified

| Input | Bytes | SHA-256 |
|---|---:|---|
| Implementation Allowlist Draft 1 | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |
| DECISIONS.md through D-206 | 210,318 | `952AA9D36DD146EECADE749A1D6E7478D0111B0E90B0B8177D771F739D47D364` |
| TASK_APPROVAL.md through D-205 | 405,907 | `AE1410D5DF706A77AD4AF25CDED6B368D0F3392BAB74B8A967397784F00FDDBC` |
| PROJECT_CONTEXT.md | 83,183 | `317D947803D78F1F78D2DA9BEA8E9DF3F718DE8965DFD57E1A665A0A5F1BE612` |
| SOURCE_REGISTER.md | 115,027 | `0093F8CCE26A526D72C8B940BE8CCE250DB78A9AE852B4834F3ABB639965081A` |
| Draft 18 | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| Draft 18 cold review | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| Adopted Rev67 SRS | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |

All 15 E-file pins and 6 R-file pins matched. All 4 N paths were absent.

## Review result

The prior P2 is resolved: D-206 and the allowlist require HTTP 409 `STALE_REVISION` on the cancel route to include top-level integer `current_version` equal to the current `story.runs.revision`. It appears only on that stale-cancel error in the Section 9.8 envelope. The successful HTTP 202 body remains exactly D-204's three keys, with D-201 `run_revision` nested in `story_run`.

The age-scope P3 is resolved: the allowlist applies trusted ages 36/120 accepted and 121/155 rejected only to new-run admission. It preserves the D-205 specification-only boundary, D-206 response-contract-only boundary, exact E/N path scope and command ceilings. Draft 18 remains unchanged and pinned; D-206 and the allowlist explicitly correct its stale-cancel current-version omission.

## P3 follow-up

Current-version details for stale-revision responses on routes other than cancel remain outside this allowlist. Track that broader Rev67 §21.4 alignment as a separate review item; do not expand this allowlist.

## Limits

This is a read-only plan review, not implementation execution or launch. No tests, validators, backend execution, database or migration commands, Docker, install, network, provider, or Modal commands were run. `OWNER_MODAL_CALL_APPROVED=NO`.
