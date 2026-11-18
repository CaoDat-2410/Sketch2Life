# M2-S2 Shared OpenAPI Mapper Fix Draft 10 — Cold Review Evidence

**Date:** 2026-11-16  
**Verdict:** ACCEPT WITH CORRECTIONS — planning review only  
**Reviewed target:** `plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT10_20261116.md`  
**Target pin:** 63,397 bytes; SHA-256 `8D486CEC1F84B4A195124A13851142827EDE7BFBB635E9F5737798C45531E6EA`

## Review provenance and receipt

- Independent cold-review thread: `01a1e352-f69f-7220-a2d0-c76110eaf467`.
- Initial request ID: `m2s2-openapi-mapper-draft10-cold-review-20261116-8d486cec`.
- Complete §§6–7 continuation request ID: `m2s2-openapi-mapper-draft10-cold-review-send-sections6-7-20261116`.
- The fresh thread used the same BE worktree, read-only sandbox, network disabled, approval policy `never`, and no parent/forked context.
- The reviewer first confirmed all ten section headings and the prior-finding trace but reported that the initial payload truncated inside §6 and resumed mid-§7. The complete §§6–7 were supplied in the same thread. The reviewer then confirmed complete receipt of §§1–10, the trace, and the Draft 6–9 evidence excerpts before issuing its verdict. No second thread was created.
- The reviewer assessed the supplied plan and excerpts. It did not run commands, independently recalculate hashes, or inspect repository state.

## Verdict and remaining finding

**ACCEPT WITH CORRECTIONS.** The plan’s Draft 9 collision correction works for a root that already exists at preflight: it reports the collision and stops before writing there. After successful root creation, the card writes the hash manifest before later failure throws and records missing or unreadable artifacts, exit status, and report state. This preserves the Draft 7 failure-evidence requirement.

**P2 — §6, comparison-root creation failure:** The prose requires creation failure to stop before any write, but the card’s `New-Item ... | Out-Null` has no explicit terminating-error handling or success check. A creation error could leave execution proceeding to later steps. Make creation failure stop immediately and confirm the new root was successfully created before invoking the comparator or writing artifacts. Keep the no-manifest rule for a failed root creation and the manifest-before-later-failure rule for a successfully created root.

The reviewer found no P1. The owner directed that no Draft 11 be created. This evidence does not authorize another planning draft, baseline, tests, validation, implementation, approval, S2 closure, S3, or launch.

## Trace and checks confirmed

The reviewer confirmed that the supplied trace supports review of all four Draft 6 findings and the Draft 7–9 responses:

- pytest/exporter environment separation;
- comparator report producer and handoff;
- request-ID inventory OPEN and fail-closed;
- engine disposal described as normal-path only;
- normalized environment identity;
- failure-artifact hashing;
- N-path `ABSENT`/`null` to `PRESENT`/actual-hash handling; and
- the Draft 9 output-root collision boundary.

Option A, allowlist Choice A, and the Draft 5 provenance boundary are preserved. Draft 10 remains planning-only and makes no implementation, baseline, test, approval, or launch claim.

## Remaining evidence gaps

- Runtime behavior, lock-matched environment provenance, exporter/comparator execution, and OS-level egress blocking remain unverified and gated for future approval.
- The exact request-ID method/path and JSON-pointer inventory remains OPEN and fail-closed.
