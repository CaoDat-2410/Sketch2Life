# Plan Rev58 — BM04 workflow and CI/CD SRS alignment

- **Feature:** FEAT-063 system architecture rearchitecture
- **Date:** 2026-11-09 (Asia/Saigon)
- **Change type:** Canonical SRS documentation update
- **Approval basis:** Direct owner instruction in the current conversation; direct DOCX editing was subsequently authorized after no Word Document Control session was available.

## Goal

Align the canonical FEAT-063 v2.5-draft SRS with the BM04 working workflow and delivery scenario while preserving the distinction between target design and current repository evidence.

## Exact change scope

- Update the CI/release gates in §25.5 with the current GitHub Actions CI job set and a concrete, provider-neutral CD scenario.
- Add the synthetic “no eligible sample child” outcome to the SRS acceptance scenarios without resolving broader product-selection or consent policy by implication.
- Add a dated §32 source snapshot for the repository CI workflow and confirm that no CD workflow exists in `.github/workflows` at the inspected revision.
- Update the document update date and v2.5-draft change record. Keep the same canonical SRS path and version family; it remains a draft.

## Acceptance criteria

- **AC01 — SRS authority:** no older SRS is used; the canonical file remains v2.5-draft and unsigned.
- **AC02 — CI source:** the named triggers, runtimes, repository validators, backend test paths and three UI checks match `.github/workflows/ci.yml` and commit `18150aa5`.
- **AC03 — CD scenario:** stages, branch/tag events, artifact reuse, synthetic smoke checks, health checks and rollback are explicit; the repository is not described as having deployed them.
- **AC04 — Workflow consistency:** synthetic acceptance for no eligible child matches BM04 and does not claim a final consent/eligibility policy.
- **AC05 — Preservation:** no product requirement, data model, production hosting decision, code, API or migration changes are introduced; existing local SRS edits outside the exact patch remain intact.
- **AC06 — Evidence:** source hash, output hash, inspected Git commit, changed headings and consistency findings are recorded in FEAT-063 evidence/status/context/decisions.

## Limits

No product tests, build, runtime/deployment, provider/payment operation, production topology selection, commit or push is authorized by this plan.
