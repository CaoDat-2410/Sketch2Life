# FEAT-083 status

- **Status:** SOURCE_CHANGES_APPLIED / RUNTIME_AND_VERIFICATION_NOT_RUN
- **Plan:** Rev1, approved durable-rotation/SRS-reconciliation amendment Rev2, approved Parent ORM mapping clarification Rev3, approved stale Qwen contract assertion amendment Rev4, and approved legacy Teacher FLUX API removal Rev5.
- **Approval:** Owner’s direct request and Rev1–Rev5 approvals recorded in `approvals/TASK_APPROVAL.md`.
- **Product authority:** Canonical FEAT-063 SRS v2.7-draft is updated through Rev75; prior history is retained and the SRS remains unsigned. Rev75 records source removal only; it does not implement a replacement SVG API.
- **Runtime:** No Modal deployment/inference, API/E2E call, emulator run or database migration execution has occurred for FEAT-083.
- **Source result:** Active Qwen workloads are pinned to Qwen3.8; activity/story/video prompt and parser updates, account-scoped topic/subject rotation source, custom-topic behavior, OpenAPI text, SRS/DTR and feature records are updated within approved scope.
- **Rev5 result:** The Teacher `/lesson-visuals` backend route, service call, UI action/preview controls, Modal dispatch/provenance, L4 envelope and current registry row have been removed. The old Teacher FLUX function and dated evidence remain historical; the shared parser rejects that workload. The separate Parent sketch-guide workload is unchanged. The target SVG illustration API remains unimplemented.
- **Verification:** Source-only review; no tests/typecheck (including the test updated under Rev4), repository security validation, database migration execution, Modal deployment/inference, API/E2E, or emulator run has been performed. Changes are not runtime-verified.
- **Branch:** `feature/fe-mobile-remediation`, worktree `.codex-worktrees/fe`; current HEAD `77635688`.
