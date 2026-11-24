# Sketch2Life SRS authority

## Canonical working SRS

For all **current product requirements and target architecture**, use only:

[`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`](../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)

- Version recorded in the document: `2.7-draft`, Rev57 base with local amendments recorded through Rev73. Rev73 is the owner-approved FEAT-081 story-output recovery clarification. The current FEAT-081 worktree copy is 723377 bytes / SHA-256 `0550909E44CF08EF4568C043508B9F20968A946F83330D28D70C20C92FED3398`. These local amendments do not constitute formal SRS sign-off or evidence that all described APIs, persistence, or runtime behavior are implemented. The SRS remains unsigned.
- Authority: the project's canonical **working baseline** for current product intent and target architecture.
- Approval state: still a draft awaiting formal owner sign-off. Calling it canonical does not claim it has been signed or approved as a final SRS.
- Companion: `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` is the matching v2.7-draft data-model companion. It supports the SRS; it is not another product SRS.

If an older SRS, feature context, plan, decision, screenshot, or generated artifact conflicts with the current product intent in this SRS, use the FEAT-063 v2.7-draft SRS. Treat §32 as dated, environment-specific implementation/source evidence, not as a replacement for target requirements in §§1–31. Record unresolved or missing requirements as open questions; do not silently import an older value or imply formal approval.

## Historical and feature-local records

These remain in the repository for provenance, implementation history, and audit. They are not alternative sources of current product requirements:

- FEAT-026 current-system SRS form and English derivative: snapshot of the then-current implementation/system description; useful for historical as-is evidence only.
- FEAT-029 Master SRS and FEAT-039 Collaborative Learning SRS versions: previous product baselines, superseded for current product intent by the FEAT-063 working SRS.
- FEAT-062 `SRS_BASELINE_DRAFT_20261026.md` and its questions: an earlier workflow draft, superseded by the FEAT-063 SRS.
- FEAT-063 files named `*_V2.2_PRESERVED_*`: preserved historical snapshots; do not use them as the current SRS.
- Other feature `CONTEXT.md`, `DECISIONS.md`, plans, and evidence: authoritative only for their feature's recorded scope/status and as-of implementation evidence. They cannot supersede the current product SRS.

Do not delete, rename, or rewrite these historical sources as part of ordinary feature work. Where a historical fact matters, cite it as historical and reconcile it explicitly against the current FEAT-063 SRS.

## Required reading order for agents

1. Read root `AGENTS.md` and this authority record.
2. Read the canonical FEAT-063 SRS above for current product requirements and target behavior.
3. Read the FEAT-063 Data Table Register only when the task requires data-model detail.
4. Read a feature's local context/plan/evidence for that feature's implementation status or provenance, not to choose current product requirements.
5. Open old SRS copies only when a task explicitly requires historical comparison or traceability; identify them as superseded in the result.

This is a repository instruction and source-routing rule. It cannot prevent someone from manually opening a historical file, so old records retain explicit local context notices where they mention prior SRS authority.

## Current FEAT-063 pointer after Rev73

As of 2026-11-21, use only `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` for current product intent. Rev73 adds the owner-approved recovery transition for a deterministic `STORY_OUTPUT_INVALID` story revision; other terminal failures remain terminal and all existing rewrite, quality, safety, consent and ownership limits remain. This local amendment does not prove that API/runtime behavior has passed verification or constitute formal SRS sign-off. Consult `DATA_TABLE_REGISTER.md` separately for its own current mapping and record any mismatch; do not infer the physical database from the SRS crosswalk. Older revisions remain historical. Diagram Input Catalog Rev57 remains a readiness handoff, not a competing requirements source.
