# Sketch2Life SRS authority

## Canonical working SRS

For all **current product requirements and target architecture**, use only:

[`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`](../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)

- Version recorded in the document: `2.7-draft`, target baseline Rev57 at `f21c6f34af1ee045caf9a0621e38376a2bfde390`, carrying forward target amendments through Rev64 and append-only as-built entries in §32 through Rev87.29 (2026-11-15). Later §32 entries document implementation evidence only; they do not amend target requirements §§1–31. Rev68 records the owner-approved M0 technical defaults and M1/M2 implementation boundary; Rev69 adds a source-only implementation snapshot in §32. It remains unsigned.
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

## Current FEAT-063 pointer after Rev87.29

As of 2026-11-15, the canonical working product source remains `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft, based on published Rev57 with target amendments through Rev64. Rev68/Rev69 and later entries through Rev87.29 are append-only as-built evidence in §32; they do not change target requirements §§1–31 or claim formal SRS sign-off. Rev87.15 records the Modal Volume import and path-coverage failure; Rev87.16 records the Qwen path-assignment fix and worker pass; Rev87.17/18 record the Parent API schema rejection/fix and one successful synthetic Parent API → Modal guide request. Rev87.19–21 record source-conditioned construction-guide output rejected by hard geometry gates. Rev87.22 returned an API-valid guide whose rendered geometry failed visual acceptance. Rev87.26/27 then tested source geometry and fixed stage mapping for one exact hash-pinned monochrome kitten: Qwen catalog-query expansion selected the real catalog source, and the seven-stage result returned HTTP 200 with all 20 source paths once and passed manual cumulative visual review. This source-specific result remains a private draft requiring adult review; other assets, colored references, Android/Firebase E2E, educator approval and child comprehension remain unverified. The Modal app was stopped. This is implementation evidence, not a new target requirement. The companion `DATA_TABLE_REGISTER.md` remains an older unsigned draft; use the feature-local Rev68 persistence crosswalk only for that SVG implementation, not as a replacement for the full DTR. Both product SRS and DTR remain unsigned. Open questions and the TO-BE/AS-BUILT separation remain in force. Diagram Input Catalog Rev57 remains a readiness handoff, not a competing requirements source.

Rev87.28 adds a source-specific offline correction: eye-detail segments 10–15 now appear together in one stage, and local rendering from the saved Rev87.27 response visually confirms the paired-eye step. Focused worker tests passed 50/50. No Modal inference or deployment was performed; the saved Rev87.27 live response remains seven stages. This is as-built evidence only, recorded in SRS §32.38 and EV-063-122; §§1–31 remain unchanged.

Rev87.29 tested generic Parent catalog selection once each for elephant and fish on real Modal/Qwen3.5. Both API responses returned 200 but failed manual review: the elephant instructions/stage grouping were incoherent, and the fish query selected a kitchen-scale SVG and emitted repeated/mixed-language copy. The butterfly bundled guide also failed pre-dispatch because 39 paths exceed the API's 32-path cap. The app is stopped. See SRS §32.39 and EV-063-123. This is environment-specific as-built evidence only; generic non-kitten guide generation is not established as reliable, and target §§1–31 remain unchanged.
