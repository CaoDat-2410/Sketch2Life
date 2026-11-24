# FEAT-083 task approval

## Plan Rev1 — Qwen3.8, everyday quality, and rotating Parent catalog

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23): use Qwen3.8 throughout; make AI activities/stories/video grounded, age-appropriate and more substantive; rotate 15–20 Parent topics and their subject cards without repetition; keep free-text topic input; resolve catalog topics to catalog subjects and require subject input plus AI validation for out-of-catalog topics.
- **Approved scope:** Exact scope, file list and acceptance criteria in `plan/PLAN_REV1_QWEN38_EVERYDAY_QUALITY_TOPIC_ROTATION_20261123.md`.
- **Plan SHA-256:** `556D4488421FA5CDE2F0C8F4F97FADC9B2303114622C006B14CFE63C17155748` (`PLAN_REV1_QWEN38_EVERYDAY_QUALITY_TOPIC_ROTATION_20261123.md`, 10,707 bytes).
- **Runtime limits:** Code/documentation implementation only. No Modal deploy/download/inference, no database migration execution, no quota/safety bypass, no child data, no commit/push.
- **Constraints:** Keep FEAT-063 SRS unsigned; do not change non-Qwen models or hard business/safety gates.

## Plan Rev2 amendment — durable rotation and current SRS reconciliation

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23), extended to the 18-topic/subject rotation, non-catalog adult subject input, all active Qwen3.8 workloads, and everyday-life activity/story/video quality.
- **Approved scope:** The additional file allowlist and acceptance criteria in `plan/PLAN_REV2_AMENDMENT_20261123.md`, together with the unchanged applicable Rev1 scope.
- **Plan SHA-256:** `91BE6C93CC677F07382B728133FCBFBCD62BFE0B042BCE5FF9ADC7AA607C921F` (`PLAN_REV2_AMENDMENT_20261123.md`, 5,825 bytes).
- **Runtime limits:** Code/documentation only. No Modal deploy/download/inference, DB migration execution, emulator/E2E/API call, gate/quota bypass, commit or push.
- **Authority note:** Owner-provided instructions say local SRS amendments through Rev67; checked-in `SRS_AUTHORITY.md` and canonical SRS currently state Rev73. Preserve both histories, reconcile the checked-in authority pointer and append Rev74 without rewriting prior entries; keep unsigned.

## Plan Rev3 amendment — Parent ORM mapping path

- **Status:** APPROVED under the owner’s direct instruction to implement the approved FEAT-083 work.
- **Approver:** Project owner, direct implementation request in this conversation (2026-11-23), continuing the approved Rev1/Rev2 implementation.
- **Approved scope:** The single additional ORM mapping file and acceptance criteria in `plan/PLAN_REV3_ORM_MODEL_FILE_ADDENDUM_20261123.md`.
- **Plan SHA-256:** `F843DDFAC8FBA599C59CD6EA8147F01E0B9C0C50273D3C8FBAEE30A3BAC835E6` (`PLAN_REV3_ORM_MODEL_FILE_ADDENDUM_20261123.md`, 1,377 bytes).
- **Runtime limits:** No database migration execution or live database verification; all Rev1/Rev2 limits remain.

## Plan Rev4 amendment — active-model contract assertion alignment

- **Status:** APPROVED under the owner’s direct instruction in this conversation to use Qwen3.8 throughout active Qwen workloads.
- **Approved scope:** Update only the stale Qwen3.5/Qwen3.8 split assertions and affected test name in `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`, as listed in `plan/PLAN_REV4_QWEN38_CONTRACT_ASSERTION_ALIGNMENT_20261123.md`.
- **Plan SHA-256:** `46C36458953FE80AC2445AA7762F555DC36C24E43DB582D1AC8B5E201C60D6FB` (`PLAN_REV4_QWEN38_CONTRACT_ASSERTION_ALIGNMENT_20261123.md`, 1,415 bytes).
- **Limits:** Do not add tests or execute tests/typecheck; no Modal/API/E2E/runtime, database migration execution, emulator, security validation, commit or push. Preserve historical worker evidence and all hard gates.

## Plan Rev5 amendment — remove the legacy Teacher FLUX lesson-visual API

- **Status:** APPROVED by the project owner’s direct instruction in this conversation (2026-11-23): remove the obsolete API.
- **Approved scope:** Remove the Teacher `/lesson-visuals` backend route, its web UI caller and presentation controls, backend Modal dispatch/provenance, current worker-envelope/registry entry, and update existing API contract expectations as listed in `plan/PLAN_REV5_REMOVE_LEGACY_TEACHER_FLUX_API_20261123.md`.
- **Plan SHA-256:** `649FF3E992AFACB73A8459A0A70506F4EEF2C64AE755181787CA76D855E5E59B` (`PLAN_REV5_REMOVE_LEGACY_TEACHER_FLUX_API_20261123.md`, 2,107 bytes).
- **Limits:** Preserve the old Modal worker and dated evidence as historical source only; no test execution, typecheck, DB migration, Modal deploy/inference, API/E2E, emulator, security validation, commit or push. Teacher SVG illustration generation is not implemented by this amendment.
