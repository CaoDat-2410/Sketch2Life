# Sketch2Life SRS authority

## Canonical working SRS

For all **current product requirements and target architecture**, use only:

[`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`](../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)

- Version recorded in the document: `2.7-draft`, self-described as the Rev57 base with Rev58–Rev69 documentation updates and as-built notes in §32 through 2026-11-15. The file is the owner-supplied copy adopted by D-209 on 2026-11-17: 701810 bytes / SHA-256 443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021, after the D-219 FR-C-08 wording edit of 2026-11-19 (13 lines, no line moved; before it 701157 bytes / `B9B1F42D…`). Its header date (2026-11-13) is stale and the owner accepted it as is. It replaces the Rev67 selection of D-203 and the Rev68 working copy reconciled under D-208; those remain historical provenance and are no longer requirement references. The adopted copy is unsigned.
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

## Current FEAT-063 pointer after D-209

As of 2026-11-17, the canonical working product source is features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md with the exact bytes of the owner-supplied copy adopted by D-209 (701157 bytes / SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5). The owner directed that older revisions are no longer used as requirement references. The copy labels its own amendments Rev68 (SVG technical defaults) and Rev69; that Rev68 label is not the Rev68 working copy produced under D-208 (639948 bytes / SHA-256 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944), so read any older record that says Rev68 by its pin. The adopted copy does not contain the D-208 reconciliation wording; lifecycle requirements are read from the adopted copy, and D-209 records the open interpretation point for FR-C-08. The SRS is unsigned. The matching DATA_TABLE_REGISTER.md remains v2.7-draft Rev57 and is unchanged by this update. This update does not close other OPEN-OWNER decisions or supersede the TO-BE/AS-BUILT separation. The root checkout and the mobile worktree still point to Rev60 until their branches are updated. Diagram Input Catalog Rev57 remains a readiness handoff, not a competing requirements source.

## Current FEAT-063 pointer after D-219

As of 2026-11-19, the canonical working product source is the same path with 701810 bytes / SHA-256 443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021. D-219 records the documentation-only FR-C-08 wording edit applied to the D-209 bytes: 13 lines changed, no line moved, header unchanged. The section above describes the D-209 adoption and its earlier bytes; records pinned to those bytes are historical. The SRS is still unsigned.

## Current FEAT-063 pointer after Rev73

As of 2026-11-25, the canonical working product source is the same path with 718663 bytes / SHA-256 60A3022659B14E8A08FECA865520C600D8B8E1F3CEA32D3DC1740F275C49FEAB (before this edit: 716118 bytes / SHA-256 7714A5C705199E4125638C552F2F4CE4F09FA202B3738180E25B3C5259AE64BD). The owner decided to adopt SRS Rev73 only: one added sentence in BR-13, one added bounded-recovery bullet in section 6.1.1 (a new adult rewrite command after a deterministic `STORY_OUTPUT_INVALID` story failure), and one revision-history row. The three texts are copied verbatim from the source branch `origin/codex/parent-modal-e2e-20261123` at `77635688`. Rev72 of that branch is not adopted, and the quota and billing wording of the current copy is unchanged. The document remains a draft awaiting formal owner sign-off. The sections above that pin earlier bytes (D-209, D-219) and any approval or evidence record that cites an earlier SHA-256 stay as historical text and are not rewritten.
