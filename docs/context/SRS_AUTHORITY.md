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

## Current FEAT-063 pointer after Rev74

As of 2026-11-25, the canonical working product source is the same path with 720332 bytes / SHA-256 6FDD6AF189B2CC8AF3641A733B018C3A051BFEC1A9176615ABDD92410FCE28D5 (before this edit: 718663 bytes / SHA-256 60A3022659B14E8A08FECA865520C600D8B8E1F3CEA32D3DC1740F275C49FEAB). Rev74 is a minimal owner-decided change: one sentence in the "Tao story" workflow row and one in the story/storyboard model row saying that in the development environment the text workloads and drawing understanding run by default on the Qwen3.8-27B-FP8 checkpoint (owner decision of 2026-11-25), with a code-level fallback to the Qwen3.5 pin that cannot run on Modal without re-downloading the Qwen3.5 weights, plus one revision-history row. The checkpoint revision is owner-confirmed (c3a462cc3d38cf351f3b26cbd763469eeb74ef81, from the Modal volume listing of 2026-11-25); the cost, safety, licence, latency and quality conditions stay open and this is not a production approval. The document remains a draft awaiting formal owner sign-off. The sections above that pin earlier bytes (D-209, D-219, Rev73) and any approval or evidence record that cites an earlier SHA-256 stay as historical text and are not rewritten.

## Current FEAT-063 pointer after Rev75

As of 2026-11-26, the canonical working product source is the same path with 724082 bytes / SHA-256 4EB4293EB7E5A79BF765EDE4A09F19EB91F8A40AA2106A08C6495A32F20F0636 (before this edit: 720332 bytes / SHA-256 6FDD6AF189B2CC8AF3641A733B018C3A051BFEC1A9176615ABDD92410FCE28D5). The owner approved two documentation changes. First, twelve editorial fixes: the header revision range, two missing anchors, the §31.19 table-of-contents entry, one table separator, five unterminated table rows and one stray space; no requirement changed. Second, Rev75: a narrow exception to the Rev66 removal of FLUX for one optional, Teacher-requested drawing-guide picture of the Sketch Deck (section 31.21, development environment only), matching the code of commit 50e3200f; its open points are listed there. An English translation, `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_EN.md` (707332 bytes / SHA-256 FAC24F9CE247B457480469432A9CECB166F0CA73E58E3640B0595C5B78F2E4AD), sits beside it. It is machine-translated, not reviewed in full by a person, and not canonical. Contradictions found inside the SRS during this pass are not resolved by this edit. The document remains a draft awaiting formal owner sign-off. The sections above that pin earlier bytes and any approval or evidence record that cites an earlier SHA-256 stay as historical text and are not rewritten.

## Current FEAT-063 pointer after Rev76

As of 2026-11-26, the canonical working product source is the same path with 726332 bytes / SHA-256 0627ADD4F78E9E64D2A3F789A00C1C64E3ECE9C6A75A4572047CC88C80FFF9FB (before this edit: 724082 bytes / SHA-256 4EB4293EB7E5A79BF765EDE4A09F19EB91F8A40AA2106A08C6495A32F20F0636). The owner approved eight documentation fixes without a business-rule change; they are listed in the Rev76 revision row. The English copy beside it is now 709464 bytes / SHA-256 FE918D20AB3A7A6B4DA8563F62CBB116CBAFF241A64C7376B8AA6A12930D1A78; it stays machine-translated and not canonical. The other contradictions found inside the SRS still need owner decisions. The document remains a draft awaiting formal owner sign-off. The sections above that pin earlier bytes and any approval or evidence record that cites an earlier SHA-256 stay as historical text and are not rewritten.

## Current FEAT-063 pointer after Rev77

As of 2026-11-26, the canonical working product source is the same path with 728899 bytes / SHA-256 DB6385EE8A01732C468D6E928ABEC87A42B52AA149C081F29C5B0C19EB7199F2 (before this edit: 726332 bytes / SHA-256 0627ADD4F78E9E64D2A3F789A00C1C64E3ECE9C6A75A4572047CC88C80FFF9FB). The owner decided ten open points; they are listed in the Rev77 revision row. Teacher allocation enforcement exists in the billing code; its use by the video admission path was not verified here. The English copy beside it is now 711822 bytes / SHA-256 46FF10C57038E263366D000EE6C89763DE2E8A1E92ECAC9D9552C7FBEFC64B1C; it stays machine-translated and not canonical. The document remains a draft awaiting formal owner sign-off. The sections above that pin earlier bytes and any approval or evidence record that cites an earlier SHA-256 stay as historical text and are not rewritten.

## Current FEAT-063 pointer after Rev78

As of 2026-11-28, the canonical working product source is the same path with 729327 bytes / SHA-256 173D578CF88839353E3575BE0DEE630CF89999E7C8A71D928CC48F6FA6922BD0 (before this edit: 728899 bytes / SHA-256 DB6385EE8A01732C468D6E928ABEC87A42B52AA149C081F29C5B0C19EB7199F2). The owner decided to remove the MFA requirement for organization and billing admins (NFR-24, the security section, AC-28 and the NFR-24 traceability row); the Rev78 revision row records it. MFA is not implemented, and the risk it addressed has no compensating control. The English copy beside it is now 712174 bytes / SHA-256 2AC69C1BCC8687A9D3D94D759AB5EEF94ABB8E56F57A0F3C2A1A7F14E55B59C6; it stays machine-translated and not canonical. The document remains a draft awaiting formal owner sign-off. Earlier pins in the sections above and in approval or evidence records stay as historical text.
