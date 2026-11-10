# FEAT-066 evidence index

| Evidence ID | Type | Artifact | Summary / limitation |
|---|---|---|---|
| FEAT-066-EV-001 | SRS/source review | `notes/FE_UI_FULL_SRS_REVIEW_REV57_20261110.md` | Whole-FE source comparison against canonical SRS v2.7-draft Rev57. Read-only; no tests/builds/backend calls or new runtime captures. |
| FEAT-066-EV-002 | School Manager SRS + UI/UX review | `notes/SCHOOL_MANAGER_WEB_UX_REVIEW_REV57_20261110.md` | Focused review of `apps/school-manager-ui` against canonical Rev57; original local fixture preview and screenshots, before remediation. |
| FEAT-066-EV-003 | Contract inventory + remediation | `notes/SCHOOL_MANAGER_WEB_REMEDIATION_REV57_20261110.md` | Approved FE-only remediation scope and source-only API inventory; records unsupported backend dependencies. |
| FEAT-066-EV-004 | Post-remediation local UI review | `notes/SCHOOL_MANAGER_WEB_REMEDIATION_REV57_20261110.md`; `screenshots/remediation-before/`; `screenshots/remediation-after/`; `screenshots/remediation-after/capture-observations.json` | Login, M01 and M02 desktop/narrow screenshots plus tab-key and responsive-layout observations. Local preview only; API-mode roster is source-reviewed but not exercised with authenticated data. |

The older 37-screen album in FEAT-036 is historical synthetic-preview evidence; it does not establish current route coverage or tablet validation.