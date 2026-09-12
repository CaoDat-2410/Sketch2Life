# Task approval

- Status: APPROVED (P1 implementation slice; isolated FEAT-018 P2-T1 D2 image admission; and
  isolated P2-T1 D3-R2 evaluation scope. D3/P2-T1 is closed for owner-approved synthetic Cohort A
  evidence only; Cohort B, P2-T2 through P2-T5, P3, P4 and shared integration remain pending)
- Approver: Project owner direct instruction in the current conversation
- Plan revision: 2
- Requested scope: FEAT-018 revision 2 P1 implementation slice only: catalog promotion/provenance, Activity Template Library, adult context and deterministic eligibility, semantic-anchor to objective/template selection, ExperienceSpec compilation and fit validation, Gate B identity/version locking, catalog/pilot harness and feature-local evidence.
- Explicit exclusions: P2/P3/P4/shared implementation, production API/cloud, Runpod, Android release, real child/personal data, and mobile provider credentials.

## Approved P1 scope addendum — 2026-09-09

The project owner approved FEAT-018 plan revision 2 for the P1 implementation slice described above. This approval covers the P1 task IDs `FEAT018-P1-E1` through `FEAT018-P1-E5` and the original P1 catalog/context/Gate-B/harness tasks in `PERSON_1_DOMAIN.md`.

Approved P1 acceptance boundary:

- versioned 100-MVP and 20-golden catalog promotion with provenance and the ACT-0004 migration;
- curated `ActivityTemplateV1` records with objective, anchor, age, material, supervision and safety rules;
- adult-provided `P1ContextV1` and deterministic hard eligibility rules;
- `SemanticAnchorSetV1` to one `LearningFocusV1` and one compatible activity template;
- immutable `ExperienceSpecV1` compilation and proposed `ActivityFitEvaluationV1` policy;
- Gate B approval of exact activity, objective, template and spec versions;
- 100-MVP offline validation, 20-golden pilot fixtures and redacted feature-local evidence.

This approval does not authorize P2 model changes, P3 renderer implementation, P4 provider/media implementation, shared mobile/backend/gallery integration, live provider execution, production API/cloud work, Android release, or real child/personal data. The proposed revision-2 contracts remain subject to the shared contract-freeze rules; P1 may implement only its approved domain slice and its fixture-local contract adapters.

## Implementation record — 2026-09-09
- P1 fixture-only implementation completed on `codex/p1-feat018-task-plan`.
- Evidence: `evidence/metrics/P1_ENGINE_VALIDATION_20260909.json` and `evidence/notes/P1_ENGINE_IMPLEMENTATION_20260909.md`.
- Downstream P2/P3/P4/shared/live/production scope remains unimplemented and separately gated.

## Approved P2-T1 D2 scope addendum — 2026-09-10

The project owner approves FEAT-018 P2-T1 D2: the isolated image-admission implementation
specified in `evidence/P2_IMAGE_ADMISSION_SPEC_20260910.md` (`EV-018-P2-D1-SPEC-01`, revision 2),
which is the sole canonical authority for this scope. `evidence/notes/P2_RESEARCH_ROUND2_D2_IMPLEMENTATION_GOAL_20260910.md`
is a local, Git-ignored execution guide only; it carries no approval authority, this approval
does not depend on it, and it must never be cited as an approval basis.

U1 dependency decision — approved: add

```toml
image-admission = ["av==18.1.0"]
```

under `[project.optional-dependencies]` in `backend/pyproject.toml`. PyAV must never be relied
upon transitively through the `asr-faster-whisper` extra.

Approved D2 acceptance boundary:

- seven new files: `domain/understanding/image_admission.py`,
  `application/ports/image_decoder.py`, `application/services/image_admission.py`,
  `infrastructure/media_validation/av_image_decoder.py`, `tests/unit/test_image_admission.py`,
  `tests/unit/feat018_admission_manifest.py`, and one FEAT-018-local fixture manifest;
- one modified file: `backend/pyproject.toml`, limited to the U1 extra above;
- U2–U7 as locked in D1: closed pixel-format allowlist (measured profiles only, including JPEG
  `yuvj420p`); container validation before packet probing so `mjpeg` resolves deterministically
  to `UNSUPPORTED_CONTAINER`; `max_file_bytes=5_000_000`, `max_pixels=4_000_000`,
  `max_longest_edge=4096`, `max_frames=1`; EXIF as read-only reporting only, no derivative
  written; admission results remain internal, no public schema/serialization migration; the
  FEAT-018-local fixture directory and test-only manifest schema.

This approval does not authorize D3 performance/memory evaluation, Qwen/ASR integration, mobile
transport, any public-contract migration, or any FEAT-003 connection. FEAT-003 contracts,
validation, adapters, inspector, prompts, profiles, fixtures, benchmarks, scoring, and historical
evidence remain fully excluded and unchanged. P2-T1 is not complete after D2 alone; D3 evaluation
and its separately reviewed evidence remain outstanding. The later D3-R2 addendum below separately
authorizes only that evaluation scope; it does not retroactively expand D2.

## Approved P2-T1 D3-R2 evaluation addendum — 2026-09-10

The project owner directly approved
`plan/P2_D3_IMAGE_ADMISSION_EVALUATION_PLAN.md` revision D3-R2 and its recommended decisions
D3-U1 through D3-U6. This approval authorizes only the offline image-admission evaluation harness,
deterministic Cohort A fixtures/execution, optional Cohort B preparation subject to the source gate,
and sanitized draft evidence described in that plan.

Approved measurement boundary:

- one fresh subprocess per sample, using the current interpreter and bounded stdin/stdout/stderr;
- 5-second observational target classified only from `admission_elapsed_ms` around the committed
  D2 `Feat018ImageAdmission.admit()` call;
- 256-MiB observational target classified only from the approved native-working-set bracket
  `[L,U]`: `U <= target` is `WITHIN_TARGET`, `L > target` is `EXCEEDS_TARGET`, otherwise
  `INCONCLUSIVE`;
- Windows native measurement through stdlib `ctypes` and `PROCESS_MEMORY_COUNTERS_EX`, with raw
  peak/current/private values diagnostic only and no peak-to-peak classification;
- Cohort A uses 20 fresh-process repeats per homogeneous profile and dependency-free nearest-rank
  p95; Cohort B is limited to eight non-sensitive owner-reviewed images and three repeats each;
- completed sanitized JSON/Markdown requires owner review before evidence indexing or D3/P2-T1
  completion.

Cohort B execution is not yet source-approved: the owner must visually review the actual four JPEG
and four PNG candidates against the plan's exclusion list before they are hashed or executed. Until
then, implementation and Cohort A work may proceed, but Cohort B must stop at its source gate.

This approval does not authorize a production timeout/worker, dependency change, D2 behavior or
policy change, Qwen/ASR work, mobile transport, Gate A/shared integration, public-contract
migration, or any FEAT-003 edit/connection. It does not mark D3 or P2-T1 complete and does not
authorize push or PR creation.

## Owner approval and Cohort A closure - 2026-09-11

The project owner approved Formal Cohort A at commit
`c77230ca1593d5cd31098b5e58f3ff2a13d18a63`, authorized publication/indexing of the sanitized
metrics JSON and both verification reports, and closed D3/P2-T1 for the synthetic Cohort A scope
only. Cohort B remains unapproved. The approved artifacts are indexed in `evidence/README.md`; no
provider, mobile, FEAT-003 or shared-integration work is authorized by this closure.

## Owner approval and Cohort B source admission - 2026-09-12

The project owner approved the exact local B01-B08 candidate set for FEAT-018 D3-R2 Cohort B:
four JPEG files and four PNG files, as recorded in the local git-ignored candidate manifest under
`tmp/feat018-cohort-b-input-20260912/`. The manifest sets `owner_reviewed=true` and preserves the
per-file SHA-256 values. This addendum authorizes only the offline Cohort B evaluation described by
D3-R2; raw images remain local and no provider, Qwen, Whisper, mobile, FEAT-003, or shared-
integration work is authorized.
