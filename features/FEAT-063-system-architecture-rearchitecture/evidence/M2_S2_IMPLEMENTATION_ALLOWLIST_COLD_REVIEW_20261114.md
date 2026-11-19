# M2 S2 Implementation Allowlist Draft 1 — Independent Cold Review

**Review date:** 2026-11-14  
**Verdict:** READY WITH NOTES  
**Finding counts:** 0 P1, 0 P2, 1 P3

## Pinned inputs verified

| Input | Bytes | SHA-256 |
|---|---:|---|
| Implementation Allowlist Draft 1 | 14,768 | `720B717A1656CDB4928A1AA045032A4DC78F34ECE5723C93C326BE81FE3F1FBB` |
| DECISIONS.md through D-206 | 210,318 | `952AA9D36DD146EECADE749A1D6E7478D0111B0E90B0B8177D771F739D47D364` |
| Draft 18 | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| Draft 18 cold review | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| Adopted Rev67 SRS | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |

All 15 E-file pins and 6 R-file pins matched. All 4 N paths were absent.

## Review result

D-206 and the allowlist specify the cancel stale-revision response required by Rev67 §21.4: HTTP 409 `STALE_REVISION` includes top-level integer `current_version` equal to the current `story.runs.revision`. The field is included only for this stale-cancel error in the §9.8 envelope. The HTTP 202 cancel success body remains exactly the three D-204 keys, with D-201 `run_revision` inside `story_run`. The existing Parent profile error contract and mobile parser support the `current_version` name.

The allowlist also limits trusted ages 121 and 155 months to new-run admission, keeps `parent_ai._story_response` in its exact E-file scope, ties `request_id` to the existing UUID contract, and preserves the approved S2 boundaries. Draft 18 remains unchanged and hard-pinned; D-206 and the allowlist expressly correct its omission on stale-cancel current-version detail.

## P3 follow-up

The allowlist covers the cancel-specific stale response only. Alignment of stale-revision responses on other routes with Rev67 §21.4 remains a separate review item. Do not expand this allowlist to other routes.

## Limits

This is a read-only plan review, not implementation approval or launch authorization. No tests, validators, backend execution, database or migration commands, Docker, install, network, provider, or Modal commands were run. Draft 18's approval under D-205 is specification-only; D-206 is a response-contract decision only. `OWNER_MODAL_CALL_APPROVED=NO`.
