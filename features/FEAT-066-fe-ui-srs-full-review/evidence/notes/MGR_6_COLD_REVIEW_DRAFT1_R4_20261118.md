# MGR-6 Draft 1 Independent Cold Review — R4

- Review date: 2026-11-18.
- Review type: fresh-context, read-only planning review.
- Review status: ACCEPT WITH NOTES; one P2 scope ambiguity was recorded.
- This review is historical to the reviewed plan pin below and is superseded by R5 for the corrected FE-gate wording.

## Reviewed pin

| Input | Bytes | SHA-256 | Result |
|---|---:|---|---|
| MGR-6 exact immutable lesson-version review plan | 23,688 | 3CDAFDF45D5FD6EFD3925E664B2F27B2E3B8AF1AB7B035621E30651C637ABC86 | Exact pin matched; full plan and relevant SRS sections read. |

## Findings

- P2 — FE gate scope ambiguity, plan section “FE behavior observed and target gate,” line 79. The plan said Manager approve/request-changes must remain “unavailable for integration” while also stating that the existing ID-only guard may enable those buttons. The reviewer requested clarity whether the gate blocks only new MGR-9 work or instructs changing/disabling existing controls; the latter was not authorized by the plan.
- P3 — Related citation note outside this plan: the MGR-7 package line 63 labels Rev60 lines 2536–2538 as §31.3, but those lines are within §31.2. The MGR-6 plan's corrected citations at lines 14–15 distinguish §31.2 from §31.3. The MGR-7 package was outside this maintenance scope and was not edited.

## Follow-up disposition

The MGR-6 plan's FE-gate paragraph was clarified in place: the new MGR-9 exact-version slice remains blocked; existing wired controls may still enable under their ID-only guard; this plan neither authorizes nor directs changing those controls; any separate gating change requires an explicit owner decision. The resulting full plan pin was independently reviewed in R5.

## Review limits

Read-only full-plan review, targeted SRS/source reads, searches, hashes, and Git status only. No tests, validators, builds, runtime, database, Docker, network/provider, or Modal commands were run.
