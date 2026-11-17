# M2-S2 Shared OpenAPI Mapper Task Approval Draft 1 — Cold Review R5

## Review identity

- Review thread: 01a1e5c5-5318-7891-a6f2-11b8f2fae99a
- Review turn: 01a1e5c6-a2c2-7c61-9c76-50292ca2201f
- Request ID: m2-s2-mapper-draft1-active-main-guard-r5-20261117
- Review mode: fresh context, read-only, network disabled; no parent or fork
- Verdict: NOT READY — P1=1, P2=1, P3=1
- Target Draft 1: 237,461 bytes / SHA-256 A6A568D21C462B6FEA473855DF76B128EC238ACC2352F8AC2B086B5AE93C2127

The reviewer did not use tools or run commands. The coordinator verified the live Draft 1 size and SHA-256 before and after the review. The source/dependency table contained 13 present pins that matched and the declared N mapping-test path remained absent at preflight.

## Findings returned

### P1 — Exporter can inspect an unsafe changed path before rejecting it

The reviewer found that source-inventory validation in the exporter does not reject colons or non-printable path characters before file-kind and file-state checks inspect or hash the referenced files. Comparator validation occurs later and cannot prevent an earlier read. This conflicts with the requirement to reject unsafe paths before content access.

### P2 — Child PATH may not locate Git

The exporter invokes Git by executable name for branch, HEAD, and status. The declared child PATH is limited to the interpreter directory and System32 and does not pin or invoke Git by absolute path. The reviewer notes that on a typical Windows installation Git may be outside those directories, preventing export before source-state evidence is produced.

### P3 — pytest-bootstrap.py has duplicate main definitions

The reviewer observed that pytest-bootstrap.py still defines main twice, leaving a shadowed implementation in the reviewed payload.

## Review limitation

The reviewer reported visible truncation markers in the supplied parts and could not independently verify the target size or digest. It described its assessment as limited to visible supplied text. The coordinator-provided pin above was independently hashed from the live file, but the returned review therefore does not establish a complete independent byte-for-byte review of the exact target.

## Gate outcome

The review is NOT READY and has P1/P2 findings. The single correction and review authorized by the owner are consumed. No further correction or review is authorized by that task. No mapper approval, baseline export, test, or implementation is authorized by this result. Draft 10 retains its historical ACCEPT WITH CORRECTIONS verdict and ComparisonRoot P2. S2 remains PARTIAL / NOT COMPLETE.