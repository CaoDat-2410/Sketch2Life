# Sketch2Life SRS authority

## Canonical working SRS

For current product requirements and target architecture, use only the FEAT-063 file:

[`features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`](../../features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)

- Authority: v2.7-draft, Rev57 baseline with documented amendments through Rev67.
- Approval: unsigned; it remains a working draft pending formal owner sign-off.
- §§1–31 define target requirements. §32 contains dated, environment-specific source/runtime evidence and does not replace the target requirements.
- `DATA_TABLE_REGISTER.md` is a data-model companion, not a second product SRS. Where it or another record conflicts with the canonical SRS, preserve the discrepancy and do not silently promote the conflicting text.

The user's repository instructions make this FEAT-063 SRS the current baseline. Later-revision text in feature-local plans, decisions, reports, screenshots, or code comments is provenance for that feature only; it does not update product requirements or SRS authority. Do not treat a local amendment or implementation as formal sign-off.

## Historical and feature-local records

Older SRS copies, feature contexts, plans, decisions, screenshots, generated assets, and implementation reports remain in the repository for provenance. They are not alternative sources of current product requirements. Consult them only for a requested historical comparison or for evidence within their named feature, and label the date/scope of that evidence.

If a current requirement is missing or conflicts with a historical or feature-local record, keep the question open and report it. Do not import an older requirement silently, and do not delete or rewrite historical records as ordinary cleanup.

## Required reading order

1. Read root `AGENTS.md` and this authority record.
2. Read the canonical FEAT-063 SRS above for current requirements.
3. Read the Data Table Register only when the task needs data-model detail.
4. Read feature context/plans/evidence for that feature's scope and implementation provenance, not to select product requirements.
5. Open older SRS copies only for explicit historical comparison or traceability.
