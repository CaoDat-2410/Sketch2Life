# M2-S2 Shared OpenAPI Mapper Fix Draft 10 — disposition of the review P2 (ComparisonRoot creation)

**Date:** 2026-11-17
**Status: PROPOSED DISPOSITION — FOR OWNER REVIEW.** Prepared by the coordinating Claude session. It does not edit Draft 10 or its cold-review evidence, does not change that review's verdict, and grants no approval, baseline, test, implementation or launch authority.

## The finding

- Draft 10: `plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT10_20261116.md`, 63,397 bytes, SHA-256 `8D486CEC1F84B4A195124A13851142827EDE7BFBB635E9F5737798C45531E6EA`.
- Its cold review: `evidence/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT10_COLD_REVIEW_20261116.md`, 3,508 bytes, SHA-256 `3550014378EB0D27B7D91AE56C8032948ECF0752B8956E5C28CFBF5BF76897FA`. Verdict: **ACCEPT WITH CORRECTIONS**, no P1, one P2.
- The P2 (§6): the card's `New-Item ... | Out-Null` for the comparison root has no explicit terminating-error handling or success check, so a creation error could let execution continue. Required: make creation failure stop immediately; confirm the new root was created before invoking the comparator or writing artifacts; keep the no-manifest rule for a failed creation and the manifest-before-later-failure rule for a successfully created root.
- The owner directed that no Draft 11 be created. The correction therefore lives in the command card that will actually be executed, which is the Compare card of the Mapper Task Approval Draft 1.

## Where the correction is

Mapper Task Approval Draft 1: `plan/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_20261116.md`, 321,800 bytes, SHA-256 `4EAEA5340B1369E2A484FE86DE04AD6A1D949C2E838295C17988B3BCEC9666C3`, section "Comparator and mandatory ComparisonRoot guard".

| Requirement of the P2 | How the Draft 1 Compare card and runner meet it |
|---|---|
| Creation failure stops immediately | The card starts with `$ErrorActionPreference = 'Stop'` and creates the root with `New-Item -ItemType Directory -Path $ComparisonRoot -ErrorAction Stop`, so a creation error is terminating. |
| Confirm the root was created before the comparator or any artifact | Immediately after creation the card resolves the created path with the no-reparse helper and throws unless it is an existing directory, equals the intended full path and is a direct child of the verified `backend\tmp`. Before creation it rejects a GUID collision and checks that the intended path is a direct child of `backend\tmp`. |
| No manifest when creation fails | The first write of `sha256.txt` comes only after that verification, so a failed or unverified creation writes nothing into the root. |
| Manifest before later failures | After verification the card writes the initial `sha256.txt`, then verifies every pinned input hash and rewrites the manifest with those rows before launching the comparator; later failures retain it. The runner appends its own rows under a marker line and keeps the card's rows. |
| Comparator not launched on an unverified root | The runner accepts the Compare action only with `-RootAlreadyCreated`, requires the root to be an existing directory with the approved name form, and repeats the direct-child and reparse checks before writing `run-manifest.json` or launching the child. |

## Evidence that the correction was reviewed and exercised

- Full cold reviews of the preceding Draft 1 pin (318,297 bytes, SHA-256 `9A56F151240940FD3119D1B2F5B0CDB7575F743C0764A2A225A504579E18ACA0`), which already contained this card: R14 (`evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R14_20261117.md`, recorded verdict NOT READY with 0 P1, 0 P2 and 3 P3, none of them about this card) and R15 (`evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R15_20261117.md`, ACCEPT in a read-only sandbox). Both confirmed that Draft 10's verdict and its P2 are stated unchanged in Draft 1. The correction made after R14/R15 changed the child bootstrap and wording in §5 and §7 only; the Compare card text is the same in the pin cited above. The delta review of those later changes is `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_DELTA_REVIEW_R16_20261117.md` (ACCEPT WITH NOTES).
- This note itself was reviewed by an independent session (R17, `claude-sonnet-5-5`, effort high, read-only by instruction, session `local_0fa8a19c-c006-4849-adbf-b4e683ca428b`): ACCEPT WITH NOTES, 0 P1, 0 P2, 3 P3 on citations, all applied here; every table row was judged supported by the card and runner text.
- R12 asked for two bare `Get-Item` calls in this card to be wrapped; that was done before R14/R15.
- The payload rehearsal of 2026-11-17 (`evidence/M2_S2_SHARED_OPENAPI_MAPPER_PAYLOAD_REHEARSAL_20261117.md`) ran the runner's Compare action against a pre-created comparison root on a synthetic worktree: the runner accepted the root, the comparator wrote its report, and `sha256.txt` kept the initial line and gained the runner's rows. The PowerShell card itself was not executed in the rehearsal; the directory was created by the rehearsal driver.

## Limits

- The PowerShell Compare card has not been executed. A real creation failure (for example a permission error on `backend\tmp`) has not been provoked.
- The card's `throw` and `-ErrorAction Stop` halt execution only when the card runs as one script or one pasted block. Typed line by line in an interactive console, later lines would still run after an error; the Task Approval must therefore pin the run method (saved as a `.ps1` file and executed as a whole).
- If a pinned input hash differs, the manifest that is retained is the single guard line written after root verification; the per-input rows are written only when all hashes match.
- Draft 10's own text still contains the unguarded `New-Item`; Draft 10 is a superseded planning input and its card must not be executed.

## Owner disposition recorded

On 2026-11-17 the owner (Person 2) accepted this disposition in chat (reply "Chấp nhận" to the question whether to accept the Draft 10 P2 disposition). The Draft 10 review P2 is therefore treated as addressed by the Mapper Task Approval Draft 1 Compare card; Draft 10's recorded verdict (ACCEPT WITH CORRECTIONS) is unchanged. This acceptance is a planning disposition only: it is not the formal Task Approval, and it must be restated in that approval record when the owner approves the mapper task.

## Proposed owner disposition (as put to the owner)

Treat the Draft 10 review P2 as **addressed by the Mapper Task Approval Draft 1 Compare card**, with Draft 10's verdict left as recorded (ACCEPT WITH CORRECTIONS). If the owner accepts this, the acceptance should be recorded together with the formal Task Approval for the mapper task; until then the P2 remains open.
